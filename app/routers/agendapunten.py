from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_session, API_SERVER
from app.models import AgendapuntDB
from app.schemas import (
    Agendapunt,
    AgendapuntZonderPid,
    PaginatedAgendapuntList,
    ErrorResponse,
    Gemeente,
    Provincie,
    Waterschap,
    VerwijzingNaarResource,
)
import uuid

router = APIRouter(prefix="/agendapunten", tags=["Agendapunten"])


def db_to_schema(db_agendapunt: AgendapuntDB) -> Agendapunt:
    """Convert database model to schema"""
    # Construct organisatie based on type
    if db_agendapunt.organisatie_type == "gemeente":
        organisatie = Gemeente(
            gemeente=db_agendapunt.organisatie_code,
            naam=db_agendapunt.organisatie_naam,
        )
    elif db_agendapunt.organisatie_type == "provincie":
        organisatie = Provincie(
            provincie=db_agendapunt.organisatie_code,
            naam=db_agendapunt.organisatie_naam,
        )
    else:
        organisatie = Waterschap(
            waterschap=db_agendapunt.organisatie_code,
            naam=db_agendapunt.organisatie_naam,
        )
    
    # Construct vergadering reference
    vergadering_ref = VerwijzingNaarResource(
        id=str(db_agendapunt.vergadering_id) if db_agendapunt.vergadering_id else "",
        url=f"/vergaderingen/{db_agendapunt.vergadering_id}" if db_agendapunt.vergadering_id else None,
    )
    
    # Construct hoofdagendapunt reference if exists
    hoofdagendapunt_ref = None
    if db_agendapunt.hoofdagendapunt_id:
        hoofdagendapunt_ref = VerwijzingNaarResource(
            id=str(db_agendapunt.hoofdagendapunt_id),
            url=f"/agendapunten/{db_agendapunt.hoofdagendapunt_id}",
        )
    
    return Agendapunt(
        pid=db_agendapunt.pid,
        webpaginalink=db_agendapunt.webpaginalink,
        organisatie=organisatie,
        dossiertype=db_agendapunt.dossiertype,
        agendapuntnaam=db_agendapunt.agendapuntnaam,
        vergadering=vergadering_ref,
        hoofdagendapunt=hoofdagendapunt_ref,
        omschrijving=db_agendapunt.omschrijving,
        volgnummer=db_agendapunt.volgnummer,
        tussenkop=db_agendapunt.tussenkop,
        overig=db_agendapunt.overig,
        starttijd=db_agendapunt.starttijd,
        eindtijd=db_agendapunt.eindtijd,
        locatie=db_agendapunt.locatie,
        geplandvolgnummer=db_agendapunt.geplandvolgnummer,
        geplandeeindtijd=db_agendapunt.geplandeeindtijd,
        geplandestarttijd=db_agendapunt.geplandestarttijd,
        indicatiehamerstuk=db_agendapunt.indicatiehamerstuk,
        indicatiebehandeld=db_agendapunt.indicatiebehandeld,
        indicatiebesloten=db_agendapunt.indicatiebesloten,
    )


@router.get("", response_model=PaginatedAgendapuntList)
def get_agendapunten(session: Session = Depends(get_session)):
    """Alle agendapunten opvragen"""
    statement = select(AgendapuntDB)
    agendapunten = session.exec(statement).all()
    
    results = [db_to_schema(ap) for ap in agendapunten]
    
    return PaginatedAgendapuntList(
        next=None,
        previous=None,
        results=results,
    )


@router.post("", response_model=Agendapunt, status_code=status.HTTP_201_CREATED)
def post_agendapunt(
    agendapunt: AgendapuntZonderPid,
    session: Session = Depends(get_session),
):
    """Het vastleggen van een agendapunt"""
    # Extract organisatie data
    organisatie = agendapunt.organisatie
    if isinstance(organisatie, Gemeente):
        org_type = "gemeente"
        org_code = organisatie.gemeente
    elif isinstance(organisatie, Provincie):
        org_type = "provincie"
        org_code = organisatie.provincie
    else:
        org_type = "waterschap"
        org_code = organisatie.waterschap
    
    # Create database object
    # Generate pid as URL with UUID
    pid = f"{API_SERVER.rstrip('/')}/agendapunten/{uuid.uuid4()}"
    
    # Try to convert ids to int, otherwise skip (external references)
    vergadering_id = None
    if agendapunt.vergadering and agendapunt.vergadering.id:
        try:
            vergadering_id = int(agendapunt.vergadering.id)
        except (ValueError, TypeError):
            pass
    
    hoofdagendapunt_id = None
    if agendapunt.hoofdagendapunt:
        try:
            hoofdagendapunt_id = int(agendapunt.hoofdagendapunt.id)
        except (ValueError, TypeError):
            pass
    
    db_agendapunt = AgendapuntDB(
        pid=pid,
        webpaginalink=agendapunt.webpaginalink,
        organisatie_type=org_type,
        organisatie_code=org_code,
        organisatie_naam=organisatie.naam,
        dossiertype=agendapunt.dossiertype,
        agendapuntnaam=agendapunt.agendapuntnaam,
        vergadering_id=vergadering_id,
        hoofdagendapunt_id=hoofdagendapunt_id,
        omschrijving=agendapunt.omschrijving,
        volgnummer=agendapunt.volgnummer,
        tussenkop=agendapunt.tussenkop,
        overig=agendapunt.overig,
        starttijd=agendapunt.starttijd,
        eindtijd=agendapunt.eindtijd,
        locatie=agendapunt.locatie,
        geplandvolgnummer=agendapunt.geplandvolgnummer,
        geplandeeindtijd=agendapunt.geplandeeindtijd,
        geplandestarttijd=agendapunt.geplandestarttijd,
        indicatiehamerstuk=agendapunt.indicatiehamerstuk,
        indicatiebehandeld=agendapunt.indicatiebehandeld,
        indicatiebesloten=agendapunt.indicatiebesloten,
    )
    
    session.add(db_agendapunt)
    session.commit()
    session.refresh(db_agendapunt)
    
    return db_to_schema(db_agendapunt)


@router.get("/{id}", response_model=Agendapunt)
def get_agendapunt(id: str, session: Session = Depends(get_session)):
    """Een specifiek agendapunt opvragen"""
    statement = select(AgendapuntDB).where(AgendapuntDB.pid == id)
    agendapunt = session.exec(statement).first()
    
    if not agendapunt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="De gevraagde resource is niet gevonden.",
        )
    
    return db_to_schema(agendapunt)


@router.put("/{id}", response_model=Agendapunt, status_code=status.HTTP_201_CREATED)
def put_agendapunt(
    id: str,
    agendapunt: Agendapunt,
    session: Session = Depends(get_session),
):
    """Het wijzigen van een agendapunt"""
    statement = select(AgendapuntDB).where(AgendapuntDB.pid == id)
    db_agendapunt = session.exec(statement).first()
    
    if not db_agendapunt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="De gevraagde resource is niet gevonden.",
        )
    
    # Update fields
    organisatie = agendapunt.organisatie
    if isinstance(organisatie, Gemeente):
        db_agendapunt.organisatie_type = "gemeente"
        db_agendapunt.organisatie_code = organisatie.gemeente
    elif isinstance(organisatie, Provincie):
        db_agendapunt.organisatie_type = "provincie"
        db_agendapunt.organisatie_code = organisatie.provincie
    else:
        db_agendapunt.organisatie_type = "waterschap"
        db_agendapunt.organisatie_code = organisatie.waterschap
    
    db_agendapunt.organisatie_naam = organisatie.naam
    db_agendapunt.webpaginalink = agendapunt.webpaginalink
    db_agendapunt.dossiertype = agendapunt.dossiertype
    db_agendapunt.agendapuntnaam = agendapunt.agendapuntnaam
    
    # Try to convert ids to int
    if agendapunt.vergadering and agendapunt.vergadering.id:
        try:
            db_agendapunt.vergadering_id = int(agendapunt.vergadering.id)
        except (ValueError, TypeError):
            pass
    else:
        db_agendapunt.vergadering_id = None
    
    if agendapunt.hoofdagendapunt:
        try:
            db_agendapunt.hoofdagendapunt_id = int(agendapunt.hoofdagendapunt.id)
        except (ValueError, TypeError):
            pass
    else:
        db_agendapunt.hoofdagendapunt_id = None
    db_agendapunt.omschrijving = agendapunt.omschrijving
    db_agendapunt.volgnummer = agendapunt.volgnummer
    db_agendapunt.tussenkop = agendapunt.tussenkop
    db_agendapunt.overig = agendapunt.overig
    db_agendapunt.starttijd = agendapunt.starttijd
    db_agendapunt.eindtijd = agendapunt.eindtijd
    db_agendapunt.locatie = agendapunt.locatie
    db_agendapunt.geplandvolgnummer = agendapunt.geplandvolgnummer
    db_agendapunt.geplandeeindtijd = agendapunt.geplandeeindtijd
    db_agendapunt.geplandestarttijd = agendapunt.geplandestarttijd
    db_agendapunt.indicatiehamerstuk = agendapunt.indicatiehamerstuk
    db_agendapunt.indicatiebehandeld = agendapunt.indicatiebehandeld
    db_agendapunt.indicatiebesloten = agendapunt.indicatiebesloten
    
    session.add(db_agendapunt)
    session.commit()
    session.refresh(db_agendapunt)
    
    return db_to_schema(db_agendapunt)


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def del_agendapunt(id: str, session: Session = Depends(get_session)):
    """Het bericht voor het verwijderen van een agendapunt"""
    statement = select(AgendapuntDB).where(AgendapuntDB.pid == id)
    agendapunt = session.exec(statement).first()
    
    if not agendapunt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="De gevraagde resource is niet gevonden.",
        )
    
    session.delete(agendapunt)
    session.commit()
    
    return {"message": "Verwijderactie geslaagd"}
