from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlmodel import Session, select
from app.database import get_session, API_SERVER
from app.models import InformatieObjectDB, AgendapuntDB
from app.schemas import (
    InformatieObject,
    InformatieObjectZonderPid,
    PaginatedInformatieObjectList,
    ErrorResponse,
    Gemeente,
    Provincie,
    Waterschap,
)
import uuid

router = APIRouter(prefix="/informatieobjecten", tags=["Informatieobjecten"])


def db_to_schema(db_obj: InformatieObjectDB) -> InformatieObject:
    """Convert database model to schema"""
    # Construct organisatie based on type
    if db_obj.organisatie_type == "gemeente":
        organisatie = Gemeente(
            gemeente=db_obj.organisatie_code,
            naam=db_obj.organisatie_naam,
        )
    elif db_obj.organisatie_type == "provincie":
        organisatie = Provincie(
            provincie=db_obj.organisatie_code,
            naam=db_obj.organisatie_naam,
        )
    else:
        organisatie = Waterschap(
            waterschap=db_obj.organisatie_code,
            naam=db_obj.organisatie_naam,
        )
    
    # Build agendapunten URI references
    agendapunten_refs = [
        {"id": f"{API_SERVER}/agendapunten/{agendapunt.pid_uuid}", "url": f"{API_SERVER}/agendapunten/{agendapunt.pid_uuid}"}
        for agendapunt in db_obj.agendapunten
    ] if db_obj.agendapunten else None
    
    return InformatieObject(
        pid=f"{API_SERVER}/informatieobjecten/{db_obj.pid_uuid}",
        pid_uuid=db_obj.pid_uuid,
        webpaginalink=db_obj.webpaginalink,
        organisatie=organisatie,
        titel=db_obj.titel,
        wooinformatiecategorie=db_obj.wooinformatiecategorie,
        datumingediend=db_obj.datumingediend,
        id=db_obj.external_id,
        auteur=db_obj.auteur,
        bronorganisatie=db_obj.bronorganisatie,
        creatiedatum=db_obj.creatiedatum,
        informatieobjecttype=db_obj.informatieobjecttype,
        formaat=db_obj.formaat,
        omschrijving=db_obj.omschrijving,
        taal=db_obj.taal,
        agendapunten=agendapunten_refs,
    )


@router.get("", response_model=PaginatedInformatieObjectList)
def get_informatieobjecten(session: Session = Depends(get_session)):
    """Alle informatieobjecten opvragen"""
    statement = select(InformatieObjectDB)
    informatieobjecten = session.exec(statement).all()
    
    results = [db_to_schema(obj) for obj in informatieobjecten]
    
    return PaginatedInformatieObjectList(
        next=None,
        previous=None,
        results=results,
    )


@router.post("", response_model=InformatieObject, status_code=status.HTTP_201_CREATED)
def post_informatieobject(
    informatieobject: InformatieObjectZonderPid,
    session: Session = Depends(get_session),
):
    """Het vastleggen van een informatieobject"""
    # Extract organisatie data
    organisatie = informatieobject.organisatie
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
    pid = f"{API_SERVER}/informatieobjecten/{generated_uuid}"
    
    db_obj = InformatieObjectDB(
        pid=pid,
        pid_uuid=generated_uuid,
        webpaginalink=informatieobject.webpaginalink,
        organisatie_type=org_type,
        organisatie_code=org_code,
        organisatie_naam=organisatie.naam,
        titel=informatieobject.titel,
        wooinformatiecategorie=informatieobject.wooinformatiecategorie,
        datumingediend=informatieobject.datumingediend,
        external_id=informatieobject.id,
        auteur=informatieobject.auteur,
        bronorganisatie=informatieobject.bronorganisatie,
        creatiedatum=informatieobject.creatiedatum,
        informatieobjecttype=informatieobject.informatieobjecttype,
        formaat=informatieobject.formaat,
        omschrijving=informatieobject.omschrijving,
        taal=informatieobject.taal,
        gerelateerd_informatieobject_id=informatieobject.gerelateerdinformatieobject.informatieobject if informatieobject.gerelateerdinformatieobject else None,
        gerelateerd_rol=informatieobject.gerelateerdinformatieobject.rol if informatieobject.gerelateerdinformatieobject else None,
    )
    
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    
    # Link agendapunten if provided
    if informatieobject.agendapunten:
        for agendapunt_ref in informatieobject.agendapunten:
            # Extract UUID from id (could be URL or UUID)
            agendapunt_uuid = agendapunt_ref.id
            if "/" in agendapunt_uuid:
                agendapunt_uuid = agendapunt_uuid.split("/")[-1]
            
            # Find agendapunt by pid_uuid
            agendapunt_statement = select(AgendapuntDB).where(AgendapuntDB.pid_uuid == agendapunt_uuid)
            agendapunt = session.exec(agendapunt_statement).first()
            
            if agendapunt:
                db_obj.agendapunten.append(agendapunt)
        
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
    
    return db_to_schema(db_obj)


@router.get("/{id}", response_model=InformatieObject)
def get_informatieobject(id: str, session: Session = Depends(get_session)):
    """Een specifiek informatieobject opvragen"""
    statement = select(InformatieObjectDB).where(InformatieObjectDB.pid_uuid == id)
    informatieobject = session.exec(statement).first()
    
    if not informatieobject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="De gevraagde resource is niet gevonden.",
        )
    
    return db_to_schema(informatieobject)


@router.put("/{id}", response_model=InformatieObject, status_code=status.HTTP_201_CREATED)
def put_informatieobject(
    id: str,
    informatieobject: InformatieObject,
    x_reason: str = Header(..., alias="X-Reason"),
    session: Session = Depends(get_session),
):
    """Het wijzigen van een Informatieobject"""
    statement = select(InformatieObjectDB).where(InformatieObjectDB.pid_uuid == id)
    db_obj = session.exec(statement).first()
    
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="De gevraagde resource is niet gevonden.",
        )
    
    # Update fields
    organisatie = informatieobject.organisatie
    if isinstance(organisatie, Gemeente):
        db_obj.organisatie_type = "gemeente"
        db_obj.organisatie_code = organisatie.gemeente
    elif isinstance(organisatie, Provincie):
        db_obj.organisatie_type = "provincie"
        db_obj.organisatie_code = organisatie.provincie
    else:
        db_obj.organisatie_type = "waterschap"
        db_obj.organisatie_code = organisatie.waterschap
    
    db_obj.organisatie_naam = organisatie.naam
    db_obj.webpaginalink = informatieobject.webpaginalink
    db_obj.titel = informatieobject.titel
    db_obj.pid_uuid = informatieobject.pid_uuid
    db_obj.wooinformatiecategorie = informatieobject.wooinformatiecategorie
    db_obj.datumingediend = informatieobject.datumingediend
    db_obj.external_id = informatieobject.id
    db_obj.auteur = informatieobject.auteur
    db_obj.bronorganisatie = informatieobject.bronorganisatie
    db_obj.creatiedatum = informatieobject.creatiedatum
    db_obj.informatieobjecttype = informatieobject.informatieobjecttype
    db_obj.formaat = informatieobject.formaat
    db_obj.omschrijving = informatieobject.omschrijving
    db_obj.taal = informatieobject.taal
    db_obj.gerelateerd_informatieobject_id = informatieobject.gerelateerdinformatieobject.informatieobject if informatieobject.gerelateerdinformatieobject else None
    db_obj.gerelateerd_rol = informatieobject.gerelateerdinformatieobject.rol if informatieobject.gerelateerdinformatieobject else None
    
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    
    return db_to_schema(db_obj)


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def del_informatieobject(
    id: str,
    x_reason: str = Header(..., alias="X-Reason"),
    session: Session = Depends(get_session),
):
    """Het bericht voor het verwijderen van een informatieobject"""
    statement = select(InformatieObjectDB).where(InformatieObjectDB.pid_uuid == id)
    informatieobject = session.exec(statement).first()
    
    if not informatieobject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="De gevraagde resource is niet gevonden.",
        )
    
    session.delete(informatieobject)
    session.commit()
    
    return {"message": "Verwijderactie geslaagd"}
