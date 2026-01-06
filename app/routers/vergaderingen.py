from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_session, API_SERVER
from app.models import VergaderingDB
from app.schemas import (
    Vergadering,
    VergaderingZonderPid,
    PaginatedVergaderingList,
    ErrorResponse,
    Gemeente,
    Provincie,
    Waterschap,
    Gremium,
    VerwijzingNaarResource,
)
import uuid

router = APIRouter(prefix="/vergaderingen", tags=["Vergaderingen"])


def db_to_schema(db_vergadering: VergaderingDB) -> Vergadering:
    """Convert database model to schema"""
    # Construct organisatie based on type
    if db_vergadering.organisatie_type == "gemeente":
        organisatie = Gemeente(
            gemeente=db_vergadering.organisatie_code,
            naam=db_vergadering.organisatie_naam,
        )
    elif db_vergadering.organisatie_type == "provincie":
        organisatie = Provincie(
            provincie=db_vergadering.organisatie_code,
            naam=db_vergadering.organisatie_naam,
        )
    else:
        organisatie = Waterschap(
            waterschap=db_vergadering.organisatie_code,
            naam=db_vergadering.organisatie_naam,
        )
    
    # Construct gremium if present
    gremium = None
    if db_vergadering.gremium_identificatie and db_vergadering.gremium_naam:
        gremium = Gremium(
            gremiumidentificatie=db_vergadering.gremium_identificatie,
            gremiumnaam=db_vergadering.gremium_naam,
        )
    
    # Construct hoofdvergadering reference if exists
    hoofdvergadering_ref = None
    if db_vergadering.hoofdvergadering_id:
        hoofdvergadering_ref = VerwijzingNaarResource(
            id=str(db_vergadering.hoofdvergadering_id),
            url=f"/vergaderingen/{db_vergadering.hoofdvergadering_id}",
        )
    
    # Build agendapunten URI references
    agendapunten_uris = [
        f"{API_SERVER}/agendapunten/{agendapunt.pid_uuid}"
        for agendapunt in db_vergadering.agendapunten
    ] if db_vergadering.agendapunten else []
    
    return Vergadering(
        pid=f"{API_SERVER}/vergaderingen/{db_vergadering.pid_uuid}",
        pid_uuid=db_vergadering.pid_uuid,
        webpaginalink=db_vergadering.webpaginalink,
        organisatie=organisatie,
        dossiertype=db_vergadering.dossiertype,
        naam=db_vergadering.naam,
        aanvang=db_vergadering.aanvang,
        hoofdvergadering=hoofdvergadering_ref,
        einde=db_vergadering.einde,
        georganiseerddoorgremium=gremium,
        geplandeaanvang=db_vergadering.geplandeaanvang,
        geplandeeinde=db_vergadering.geplandeeinde,
        geplandedatum=db_vergadering.geplandedatum,
        locatie=db_vergadering.locatie,
        vergaderstatus=db_vergadering.vergaderstatus,
        vergadertoelichting=db_vergadering.vergadertoelichting,
        vergaderdatum=db_vergadering.vergaderdatum,
        vergaderingstype=db_vergadering.vergaderingstype,
        agendapunten=agendapunten_uris,
    )


@router.get("", response_model=PaginatedVergaderingList)
def get_vergaderingen(session: Session = Depends(get_session)):
    """Alle vergaderingen opvragen"""
    statement = select(VergaderingDB)
    vergaderingen = session.exec(statement).all()
    
    results = [db_to_schema(v) for v in vergaderingen]
    
    return PaginatedVergaderingList(
        next=None,
        previous=None,
        results=results,
    )


@router.post("", response_model=Vergadering, status_code=status.HTTP_201_CREATED)
def post_vergadering(
    vergadering: VergaderingZonderPid,
    session: Session = Depends(get_session),
):
    """Het vastleggen van een vergadering"""
    # Extract organisatie data
    organisatie = vergadering.organisatie
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
    # Generate pid as UUID
    generated_uuid = str(uuid.uuid4())
    pid = f"{API_SERVER}/vergaderingen/{generated_uuid}"
    
    # Try to convert ids to int, otherwise skip (external references)
    hoofdvergadering_id = None
    if vergadering.hoofdvergadering:
        try:
            hoofdvergadering_id = int(vergadering.hoofdvergadering.id)
        except (ValueError, TypeError):
            pass  # External reference, not a database ID
    
    db_vergadering = VergaderingDB(
        pid=pid,
        pid_uuid=generated_uuid,
        webpaginalink=vergadering.webpaginalink,
        organisatie_type=org_type,
        organisatie_code=org_code,
        organisatie_naam=organisatie.naam,
        dossiertype=vergadering.dossiertype,
        naam=vergadering.naam,
        aanvang=vergadering.aanvang,
        hoofdvergadering_id=hoofdvergadering_id,
        einde=vergadering.einde,
        gremium_identificatie=vergadering.georganiseerddoorgremium.gremiumidentificatie if vergadering.georganiseerddoorgremium else None,
        gremium_naam=vergadering.georganiseerddoorgremium.gremiumnaam if vergadering.georganiseerddoorgremium else None,
        geplandeaanvang=vergadering.geplandeaanvang,
        geplandeeinde=vergadering.geplandeeinde,
        geplandedatum=vergadering.geplandedatum,
        locatie=vergadering.locatie,
        vergaderstatus=vergadering.vergaderstatus,
        vergadertoelichting=vergadering.vergadertoelichting,
        vergaderdatum=vergadering.vergaderdatum,
        vergaderingstype=vergadering.vergaderingstype,
    )
    
    session.add(db_vergadering)
    session.commit()
    session.refresh(db_vergadering)
    
    return db_to_schema(db_vergadering)


@router.get("/{id}", response_model=Vergadering)
def get_vergadering(id: str, session: Session = Depends(get_session)):
    """Een specifieke vergadering opvragen"""
    statement = select(VergaderingDB).where(VergaderingDB.pid_uuid == id)
    vergadering = session.exec(statement).first()
    
    if not vergadering:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="De gevraagde resource is niet gevonden.",
        )
    
    return db_to_schema(vergadering)


@router.put("/{id}", response_model=Vergadering, status_code=status.HTTP_201_CREATED)
def put_vergadering(
    id: str,
    vergadering: Vergadering,
    session: Session = Depends(get_session),
):
    """Het wijzigen van een vergadering"""
    statement = select(VergaderingDB).where(VergaderingDB.pid_uuid == id)
    db_vergadering = session.exec(statement).first()
    
    if not db_vergadering:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="De gevraagde resource is niet gevonden.",
        )
    
    # Update fields
    organisatie = vergadering.organisatie
    if isinstance(organisatie, Gemeente):
        db_vergadering.organisatie_type = "gemeente"
        db_vergadering.organisatie_code = organisatie.gemeente
    elif isinstance(organisatie, Provincie):
        db_vergadering.organisatie_type = "provincie"
        db_vergadering.organisatie_code = organisatie.provincie
    else:
        db_vergadering.organisatie_type = "waterschap"
        db_vergadering.organisatie_code = organisatie.waterschap
    
    db_vergadering.organisatie_naam = organisatie.naam
    db_vergadering.webpaginalink = vergadering.webpaginalink
    db_vergadering.dossiertype = vergadering.dossiertype
    db_vergadering.naam = vergadering.naam
    db_vergadering.pid_uuid = vergadering.pid_uuid
    db_vergadering.aanvang = vergadering.aanvang
    
    # Try to convert id to int, otherwise skip
    if vergadering.hoofdvergadering:
        try:
            db_vergadering.hoofdvergadering_id = int(vergadering.hoofdvergadering.id)
        except (ValueError, TypeError):
            pass  # External reference
    else:
        db_vergadering.hoofdvergadering_id = None
    db_vergadering.einde = vergadering.einde
    db_vergadering.gremium_identificatie = vergadering.georganiseerddoorgremium.gremiumidentificatie if vergadering.georganiseerddoorgremium else None
    db_vergadering.gremium_naam = vergadering.georganiseerddoorgremium.gremiumnaam if vergadering.georganiseerddoorgremium else None
    db_vergadering.geplandeaanvang = vergadering.geplandeaanvang
    db_vergadering.geplandeeinde = vergadering.geplandeeinde
    db_vergadering.geplandedatum = vergadering.geplandedatum
    db_vergadering.locatie = vergadering.locatie
    db_vergadering.vergaderstatus = vergadering.vergaderstatus
    db_vergadering.vergadertoelichting = vergadering.vergadertoelichting
    db_vergadering.vergaderdatum = vergadering.vergaderdatum
    db_vergadering.vergaderingstype = vergadering.vergaderingstype
    
    session.add(db_vergadering)
    session.commit()
    session.refresh(db_vergadering)
    
    return db_to_schema(db_vergadering)


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def del_vergadering(id: str, session: Session = Depends(get_session)):
    """Het bericht voor het verwijderen van een vergadering"""
    statement = select(VergaderingDB).where(VergaderingDB.pid_uuid == id)
    vergadering = session.exec(statement).first()
    
    if not vergadering:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="De gevraagde resource is niet gevonden.",
        )
    
    session.delete(vergadering)
    session.commit()
    
    return {"message": "Verwijderactie geslaagd"}
