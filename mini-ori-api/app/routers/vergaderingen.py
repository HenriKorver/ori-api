import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.database import API_SERVER, get_session
from app.models import AgendapuntDB, VergaderingDB
from app.schemas import (
    Gemeente,
    Gremium,
    PaginatedVergaderingList,
    Provincie,
    Vergadering,
    VergaderingZonderPid,
    VerwijzingNaarResource,
    Waterschap,
)

router = APIRouter(prefix="/vergaderingen", tags=["Vergaderingen"])


def _org_from_db(org_type: str, org_code: str, org_name: str):
    if org_type == "gemeente":
        return Gemeente(gemeente=org_code, naam=org_name)
    if org_type == "provincie":
        return Provincie(provincie=org_code, naam=org_name)
    return Waterschap(waterschap=org_code, naam=org_name)


def _org_to_tuple(organisatie):
    if isinstance(organisatie, Gemeente):
        return ("gemeente", organisatie.gemeente, organisatie.naam)
    if isinstance(organisatie, Provincie):
        return ("provincie", organisatie.provincie, organisatie.naam)
    return ("waterschap", organisatie.waterschap, organisatie.naam)


def _to_schema(db_obj: VergaderingDB) -> Vergadering:
    hoofdvergadering_ref = None
    if db_obj.hoofdvergadering:
        hoofdvergadering_ref = VerwijzingNaarResource(
            id=db_obj.hoofdvergadering.public_id,
            url=db_obj.hoofdvergadering.url,
        )

    gremium = None
    if db_obj.gremium_identificatie and db_obj.gremium_naam:
        gremium = Gremium(
            gremiumidentificatie=db_obj.gremium_identificatie,
            gremiumnaam=db_obj.gremium_naam,
        )

    deelvergaderingen = [deel.url for deel in db_obj.deelvergaderingen] if db_obj.deelvergaderingen else []
    agendapunten = [agenda.url for agenda in db_obj.agendapunten] if db_obj.agendapunten else []

    return Vergadering(
        id=db_obj.public_id,
        url=db_obj.url,
        webpaginalink=db_obj.webpaginalink,
        organisatie=_org_from_db(db_obj.organisatie_type, db_obj.organisatie_code, db_obj.organisatie_naam),
        dossiertype=db_obj.dossiertype,
        naam=db_obj.naam,
        aanvang=db_obj.aanvang,
        hoofdvergadering=hoofdvergadering_ref,
        einde=db_obj.einde,
        georganiseerddoorgremium=gremium,
        geplandeaanvang=db_obj.geplandeaanvang,
        geplandeeinde=db_obj.geplandeeinde,
        geplandedatum=db_obj.geplandedatum,
        locatie=db_obj.locatie,
        vergaderstatus=db_obj.vergaderstatus,
        vergadertoelichting=db_obj.vergadertoelichting,
        vergaderdatum=db_obj.vergaderdatum,
        vergaderingstype=db_obj.vergaderingstype,
        deelvergaderingen=deelvergaderingen,
        agendapunten=agendapunten,
    )


@router.get("", response_model=PaginatedVergaderingList)
def get_vergaderingen(session: Session = Depends(get_session)):
    statement = select(VergaderingDB).options(
        selectinload(VergaderingDB.deelvergaderingen),
        selectinload(VergaderingDB.agendapunten),
    )
    resultaten = session.exec(statement).all()
    return PaginatedVergaderingList(
        next=None,
        previous=None,
        results=[_to_schema(item) for item in resultaten],
    )


@router.post("", response_model=Vergadering, status_code=status.HTTP_201_CREATED)
def post_vergadering(payload: VergaderingZonderPid, session: Session = Depends(get_session)):
    org_type, org_code, org_name = _org_to_tuple(payload.organisatie)

    hoofdvergadering_id: Optional[int] = None
    if payload.hoofdvergadering:
        hoofd = session.exec(
            select(VergaderingDB).where(VergaderingDB.public_id == payload.hoofdvergadering.id)
        ).first()
        if not hoofd:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aanleverfout")
        hoofdvergadering_id = hoofd.id

    public_id = str(uuid.uuid4())
    url = f"{API_SERVER}/vergaderingen/{public_id}"

    db_obj = VergaderingDB(
        public_id=public_id,
        url=url,
        webpaginalink=payload.webpaginalink,
        organisatie_type=org_type,
        organisatie_code=org_code,
        organisatie_naam=org_name,
        dossiertype=payload.dossiertype,
        naam=payload.naam,
        aanvang=payload.aanvang,
        hoofdvergadering_id=hoofdvergadering_id,
        einde=payload.einde,
        gremium_identificatie=payload.georganiseerddoorgremium.gremiumidentificatie if payload.georganiseerddoorgremium else None,
        gremium_naam=payload.georganiseerddoorgremium.gremiumnaam if payload.georganiseerddoorgremium else None,
        geplandeaanvang=payload.geplandeaanvang,
        geplandeeinde=payload.geplandeeinde,
        geplandedatum=payload.geplandedatum,
        locatie=payload.locatie,
        vergaderstatus=payload.vergaderstatus,
        vergadertoelichting=payload.vergadertoelichting,
        vergaderdatum=payload.vergaderdatum,
        vergaderingstype=payload.vergaderingstype,
    )

    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)

    return _to_schema(db_obj)


@router.get("/{id}", response_model=Vergadering)
def get_vergadering(id: str, session: Session = Depends(get_session)):
    statement = select(VergaderingDB).where(VergaderingDB.public_id == id).options(
        selectinload(VergaderingDB.deelvergaderingen),
        selectinload(VergaderingDB.agendapunten),
    )
    db_obj = session.exec(statement).first()
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="De gevraagde resource is niet gevonden.",
        )
    return _to_schema(db_obj)


@router.put("/{id}", response_model=Vergadering, status_code=status.HTTP_201_CREATED)
def put_vergadering(id: str, payload: Vergadering, session: Session = Depends(get_session)):
    db_obj = session.exec(select(VergaderingDB).where(VergaderingDB.public_id == id)).first()
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="De gevraagde resource is niet gevonden.",
        )

    if payload.id != id or payload.url != db_obj.url:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Deze wijziging bevat aanpassingen op velden die niet mogen worden aangepast.",
        )

    incoming_org = _org_to_tuple(payload.organisatie)
    current_org = (db_obj.organisatie_type, db_obj.organisatie_code, db_obj.organisatie_naam)
    if incoming_org != current_org:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Deze wijziging bevat aanpassingen op velden die niet mogen worden aangepast.",
        )

    hoofdvergadering_id: Optional[int] = None
    if payload.hoofdvergadering:
        hoofd = session.exec(select(VergaderingDB).where(VergaderingDB.public_id == payload.hoofdvergadering.id)).first()
        if not hoofd:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aanleverfout")
        hoofdvergadering_id = hoofd.id

    db_obj.webpaginalink = payload.webpaginalink
    db_obj.dossiertype = payload.dossiertype
    db_obj.naam = payload.naam
    db_obj.aanvang = payload.aanvang
    db_obj.hoofdvergadering_id = hoofdvergadering_id
    db_obj.einde = payload.einde
    db_obj.gremium_identificatie = payload.georganiseerddoorgremium.gremiumidentificatie if payload.georganiseerddoorgremium else None
    db_obj.gremium_naam = payload.georganiseerddoorgremium.gremiumnaam if payload.georganiseerddoorgremium else None
    db_obj.geplandeaanvang = payload.geplandeaanvang
    db_obj.geplandeeinde = payload.geplandeeinde
    db_obj.geplandedatum = payload.geplandedatum
    db_obj.locatie = payload.locatie
    db_obj.vergaderstatus = payload.vergaderstatus
    db_obj.vergadertoelichting = payload.vergadertoelichting
    db_obj.vergaderdatum = payload.vergaderdatum
    db_obj.vergaderingstype = payload.vergaderingstype

    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return _to_schema(db_obj)


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def del_vergadering(id: str, session: Session = Depends(get_session)):
    db_obj = session.exec(select(VergaderingDB).where(VergaderingDB.public_id == id)).first()
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="De gevraagde resource is niet gevonden.",
        )

    session.delete(db_obj)
    session.commit()
    return {"message": "Verwijderactie geslaagd"}
