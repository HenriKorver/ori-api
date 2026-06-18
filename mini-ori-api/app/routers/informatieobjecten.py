import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.database import API_SERVER, get_session
from app.models import AgendapuntDB, InformatieObjectDB, VergaderingDB
from app.schemas import (
    Gemeente,
    InformatieObject,
    InformatieObjectZonderPid,
    PaginatedInformatieObjectList,
    Provincie,
    VerwijzingNaarResource,
    Waterschap,
)

router = APIRouter(prefix="/informatieobjecten", tags=["Informatieobjecten"])


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


def _to_schema(db_obj: InformatieObjectDB) -> InformatieObject:
    agendapunten = [
        VerwijzingNaarResource(id=ag.public_id, url=ag.url)
        for ag in db_obj.agendapunten
    ] if db_obj.agendapunten else []

    vergadering_map = {}
    if db_obj.vergadering:
        vergadering_map[db_obj.vergadering.public_id] = VerwijzingNaarResource(
            id=db_obj.vergadering.public_id,
            url=db_obj.vergadering.url,
        )

    for ag in db_obj.agendapunten or []:
        if ag.vergadering:
            vergadering_map[ag.vergadering.public_id] = VerwijzingNaarResource(
                id=ag.vergadering.public_id,
                url=ag.vergadering.url,
            )

    vergaderingen = list(vergadering_map.values())

    gerelateerd = None
    if db_obj.gerelateerd_informatieobject_id and db_obj.gerelateerd_rol:
        gerelateerd = {
            "informatieobject": db_obj.gerelateerd_informatieobject_id,
            "rol": db_obj.gerelateerd_rol,
        }

    return InformatieObject(
        id=db_obj.public_id,
        url=db_obj.url,
        webpaginalink=db_obj.webpaginalink,
        organisatie=_org_from_db(db_obj.organisatie_type, db_obj.organisatie_code, db_obj.organisatie_naam),
        titel=db_obj.titel,
        wooinformatiecategorie=db_obj.wooinformatiecategorie,
        datumingediend=db_obj.datumingediend,
        auteur=db_obj.auteur,
        bronorganisatie=db_obj.bronorganisatie,
        creatiedatum=db_obj.creatiedatum,
        informatieobjecttype=db_obj.informatieobjecttype,
        formaat=db_obj.formaat,
        omschrijving=db_obj.omschrijving,
        taal=db_obj.taal,
        vergaderingen=vergaderingen,
        agendapunten=agendapunten,
        gerelateerdinformatieobject=gerelateerd,
    )


@router.get("", response_model=PaginatedInformatieObjectList)
def get_informatieobjecten(session: Session = Depends(get_session)):
    statement = select(InformatieObjectDB).options(
        selectinload(InformatieObjectDB.agendapunten).selectinload(AgendapuntDB.vergadering),
        selectinload(InformatieObjectDB.vergadering),
    )
    resultaten = session.exec(statement).all()
    return PaginatedInformatieObjectList(next=None, previous=None, results=[_to_schema(item) for item in resultaten])


@router.post("", response_model=InformatieObject, status_code=status.HTTP_201_CREATED)
def post_informatieobject(payload: InformatieObjectZonderPid, session: Session = Depends(get_session)):
    org_type, org_code, org_name = _org_to_tuple(payload.organisatie)

    vergadering_id = None
    if payload.vergadering:
        vergadering = session.exec(select(VergaderingDB).where(VergaderingDB.public_id == payload.vergadering)).first()
        if not vergadering:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aanleverfout")
        vergadering_id = vergadering.id

    public_id = str(uuid.uuid4())
    url = f"{API_SERVER}/informatieobjecten/{public_id}"

    db_obj = InformatieObjectDB(
        public_id=public_id,
        url=url,
        vergadering_id=vergadering_id,
        webpaginalink=payload.webpaginalink,
        organisatie_type=org_type,
        organisatie_code=org_code,
        organisatie_naam=org_name,
        titel=payload.titel,
        wooinformatiecategorie=payload.wooinformatiecategorie,
        datumingediend=payload.datumingediend,
        external_id=payload.id,
        auteur=payload.auteur,
        bronorganisatie=payload.bronorganisatie,
        creatiedatum=payload.creatiedatum,
        informatieobjecttype=payload.informatieobjecttype,
        formaat=payload.formaat,
        omschrijving=payload.omschrijving,
        taal=payload.taal,
        gerelateerd_informatieobject_id=payload.gerelateerdinformatieobject.informatieobject if payload.gerelateerdinformatieobject else None,
        gerelateerd_rol=payload.gerelateerdinformatieobject.rol if payload.gerelateerdinformatieobject else None,
    )

    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)

    if payload.agendapunt:
        agendapunt = session.exec(select(AgendapuntDB).where(AgendapuntDB.public_id == payload.agendapunt)).first()
        if not agendapunt:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aanleverfout")
        db_obj.agendapunten.append(agendapunt)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)

    return _to_schema(db_obj)


@router.get("/{id}", response_model=InformatieObject)
def get_informatieobject(id: str, session: Session = Depends(get_session)):
    statement = select(InformatieObjectDB).where(InformatieObjectDB.public_id == id).options(
        selectinload(InformatieObjectDB.agendapunten).selectinload(AgendapuntDB.vergadering),
        selectinload(InformatieObjectDB.vergadering),
    )
    db_obj = session.exec(statement).first()
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="De gevraagde resource is niet gevonden.",
        )
    return _to_schema(db_obj)


@router.put("/{id}", response_model=InformatieObject, status_code=status.HTTP_201_CREATED)
def put_informatieobject(
    id: str,
    payload: InformatieObject,
    x_reason: str = Header(..., alias="X-Reason"),
    session: Session = Depends(get_session),
):
    _ = x_reason

    db_obj = session.exec(select(InformatieObjectDB).where(InformatieObjectDB.public_id == id)).first()
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

    db_obj.webpaginalink = payload.webpaginalink
    db_obj.titel = payload.titel
    db_obj.wooinformatiecategorie = payload.wooinformatiecategorie
    db_obj.datumingediend = payload.datumingediend
    db_obj.auteur = payload.auteur
    db_obj.bronorganisatie = payload.bronorganisatie
    db_obj.creatiedatum = payload.creatiedatum
    db_obj.informatieobjecttype = payload.informatieobjecttype
    db_obj.formaat = payload.formaat
    db_obj.omschrijving = payload.omschrijving
    db_obj.taal = payload.taal
    db_obj.gerelateerd_informatieobject_id = payload.gerelateerdinformatieobject.informatieobject if payload.gerelateerdinformatieobject else None
    db_obj.gerelateerd_rol = payload.gerelateerdinformatieobject.rol if payload.gerelateerdinformatieobject else None

    # Keep relation set in sync with submitted references.
    submitted_agendapunten = []
    for ref in payload.agendapunten:
        ag = session.exec(select(AgendapuntDB).where(AgendapuntDB.public_id == ref.id)).first()
        if not ag:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aanleverfout")
        submitted_agendapunten.append(ag)

    db_obj.agendapunten = submitted_agendapunten

    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return _to_schema(db_obj)


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def del_informatieobject(
    id: str,
    x_reason: str = Header(..., alias="X-Reason"),
    session: Session = Depends(get_session),
):
    _ = x_reason

    db_obj = session.exec(select(InformatieObjectDB).where(InformatieObjectDB.public_id == id)).first()
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="De gevraagde resource is niet gevonden.",
        )

    session.delete(db_obj)
    session.commit()
    return {"message": "Verwijderactie geslaagd"}
