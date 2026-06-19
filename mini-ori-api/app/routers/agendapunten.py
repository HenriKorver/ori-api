import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.database import API_SERVER, get_session
from app.models import AgendapuntDB, InformatieObjectDB, VergaderingDB
from app.schemas import (
    Agendapunt,
    AgendapuntZonderPid,
    Gemeente,
    PaginatedAgendapuntList,
    Provincie,
    VerwijzingNaarResource,
    Waterschap,
)

router = APIRouter(prefix="/agendapunten", tags=["Agendapunten"])


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


def _to_schema(db_obj: AgendapuntDB) -> Agendapunt:
    vergaderingen = []
    if db_obj.vergadering:
        vergaderingen = [
            VerwijzingNaarResource(
                id=db_obj.vergadering.public_id,
                url=db_obj.vergadering.url,
            )
        ]

    hoofdagendapunt = None
    if db_obj.hoofdagendapunt:
        hoofdagendapunt = VerwijzingNaarResource(
            id=db_obj.hoofdagendapunt.public_id,
            url=db_obj.hoofdagendapunt.url,
        )

    subagendapunten = [sub.url for sub in db_obj.subagendapunten] if db_obj.subagendapunten else []
    informatieobjecten = [obj.url for obj in db_obj.informatieobjecten] if db_obj.informatieobjecten else []

    return Agendapunt(
        id=db_obj.public_id,
        url=db_obj.url,
        vergaderingen=vergaderingen,
        webpaginalink=db_obj.webpaginalink,
        organisatie=_org_from_db(db_obj.organisatie_type, db_obj.organisatie_code, db_obj.organisatie_naam),
        dossiertype=db_obj.dossiertype,
        agendapuntnaam=db_obj.agendapuntnaam,
        hoofdagendapunt=hoofdagendapunt,
        omschrijving=db_obj.omschrijving,
        volgnummer=db_obj.volgnummer,
        subagendapunten=subagendapunten,
        tussenkop=db_obj.tussenkop,
        overig=db_obj.overig,
        starttijd=db_obj.starttijd,
        eindtijd=db_obj.eindtijd,
        locatie=db_obj.locatie,
        geplandvolgnummer=db_obj.geplandvolgnummer,
        geplandeeindtijd=db_obj.geplandeeindtijd,
        geplandestarttijd=db_obj.geplandestarttijd,
        indicatiehamerstuk=db_obj.indicatiehamerstuk,
        indicatiebehandeld=db_obj.indicatiebehandeld,
        indicatiebesloten=db_obj.indicatiebesloten,
        informatieobjecten=informatieobjecten,
    )


@router.get("", response_model=PaginatedAgendapuntList)
def get_agendapunten(session: Session = Depends(get_session)):
    statement = select(AgendapuntDB).options(
        selectinload(AgendapuntDB.vergadering),
        selectinload(AgendapuntDB.hoofdagendapunt),
        selectinload(AgendapuntDB.subagendapunten),
        selectinload(AgendapuntDB.informatieobjecten),
    )
    resultaten = session.exec(statement).all()
    return PaginatedAgendapuntList(next=None, previous=None, results=[_to_schema(item) for item in resultaten])


@router.post("", response_model=Agendapunt, status_code=status.HTTP_201_CREATED)
def post_agendapunt(payload: AgendapuntZonderPid, session: Session = Depends(get_session)):
    org_type, org_code, org_name = _org_to_tuple(payload.organisatie)

    vergadering = session.exec(select(VergaderingDB).where(VergaderingDB.public_id == payload.vergadering)).first()
    if not vergadering:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aanleverfout")

    hoofdagendapunt_id = None
    if payload.hoofdagendapunt:
        hoofd = session.exec(select(AgendapuntDB).where(AgendapuntDB.public_id == payload.hoofdagendapunt)).first()
        if not hoofd:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Het hoofdagendapunt met id '{payload.hoofdagendapunt}' is niet gevonden."
            )
        hoofdagendapunt_id = hoofd.id

    public_id = str(uuid.uuid4())
    url = f"{API_SERVER}/agendapunten/{public_id}"

    db_obj = AgendapuntDB(
        public_id=public_id,
        url=url,
        webpaginalink=payload.webpaginalink,
        organisatie_type=org_type,
        organisatie_code=org_code,
        organisatie_naam=org_name,
        dossiertype=payload.dossiertype,
        agendapuntnaam=payload.agendapuntnaam,
        vergadering_id=vergadering.id,
        hoofdagendapunt_id=hoofdagendapunt_id,
        omschrijving=payload.omschrijving,
        volgnummer=payload.volgnummer,
        tussenkop=payload.tussenkop,
        overig=payload.overig,
        starttijd=payload.starttijd,
        eindtijd=payload.eindtijd,
        locatie=payload.locatie,
        geplandvolgnummer=payload.geplandvolgnummer,
        geplandeeindtijd=payload.geplandeeindtijd,
        geplandestarttijd=payload.geplandestarttijd,
        indicatiehamerstuk=payload.indicatiehamerstuk,
        indicatiebehandeld=payload.indicatiebehandeld,
        indicatiebesloten=payload.indicatiebesloten,
    )

    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)

    return _to_schema(db_obj)


@router.get("/{id}", response_model=Agendapunt)
def get_agendapunt(id: str, session: Session = Depends(get_session)):
    statement = select(AgendapuntDB).where(AgendapuntDB.public_id == id).options(
        selectinload(AgendapuntDB.vergadering),
        selectinload(AgendapuntDB.hoofdagendapunt),
        selectinload(AgendapuntDB.subagendapunten),
        selectinload(AgendapuntDB.informatieobjecten),
    )
    db_obj = session.exec(statement).first()
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="De gevraagde resource is niet gevonden.",
        )
    return _to_schema(db_obj)


@router.put("/{id}", response_model=Agendapunt, status_code=status.HTTP_201_CREATED)
def put_agendapunt(id: str, payload: Agendapunt, session: Session = Depends(get_session)):
    db_obj = session.exec(select(AgendapuntDB).where(AgendapuntDB.public_id == id)).first()
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

    if not payload.vergaderingen:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aanleverfout")

    vergadering_ref = payload.vergaderingen[0]
    vergadering = session.exec(select(VergaderingDB).where(VergaderingDB.public_id == vergadering_ref.id)).first()
    if not vergadering:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aanleverfout")

    hoofdagendapunt_id = None
    if payload.hoofdagendapunt:
        hoofd = session.exec(select(AgendapuntDB).where(AgendapuntDB.public_id == payload.hoofdagendapunt.id)).first()
        if not hoofd:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Het hoofdagendapunt met id '{payload.hoofdagendapunt.id}' is niet gevonden."
            )
        hoofdagendapunt_id = hoofd.id

    db_obj.webpaginalink = payload.webpaginalink
    db_obj.dossiertype = payload.dossiertype
    db_obj.agendapuntnaam = payload.agendapuntnaam
    db_obj.vergadering_id = vergadering.id
    db_obj.hoofdagendapunt_id = hoofdagendapunt_id
    db_obj.omschrijving = payload.omschrijving
    db_obj.volgnummer = payload.volgnummer
    db_obj.tussenkop = payload.tussenkop
    db_obj.overig = payload.overig
    db_obj.starttijd = payload.starttijd
    db_obj.eindtijd = payload.eindtijd
    db_obj.locatie = payload.locatie
    db_obj.geplandvolgnummer = payload.geplandvolgnummer
    db_obj.geplandeeindtijd = payload.geplandeeindtijd
    db_obj.geplandestarttijd = payload.geplandestarttijd
    db_obj.indicatiehamerstuk = payload.indicatiehamerstuk
    db_obj.indicatiebehandeld = payload.indicatiebehandeld
    db_obj.indicatiebesloten = payload.indicatiebesloten

    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return _to_schema(db_obj)


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def del_agendapunt(id: str, session: Session = Depends(get_session)):
    db_obj = session.exec(select(AgendapuntDB).where(AgendapuntDB.public_id == id)).first()
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="De gevraagde resource is niet gevonden.",
        )

    session.delete(db_obj)
    session.commit()
    return {"message": "Verwijderactie geslaagd"}
