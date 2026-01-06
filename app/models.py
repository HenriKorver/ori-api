from typing import Optional, List
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum


# Database Models
class AgendapuntDB(SQLModel, table=True):
    """Agendapunt database model"""
    __tablename__ = "agendapunten"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    pid: str = Field(index=True, unique=True)
    pid_uuid: Optional[str] = Field(default=None, index=True)
    webpaginalink: Optional[str] = None
    
    # Organisatie fields (simplified - stored as JSON-like fields)
    organisatie_type: str  # gemeente, provincie, waterschap
    organisatie_code: str  # gm0363, pv27, ws0654
    organisatie_naam: str
    
    dossiertype: str
    agendapuntnaam: str
    vergadering_id: Optional[int] = Field(default=None, foreign_key="vergaderingen.id")
    hoofdagendapunt_id: Optional[int] = Field(default=None, foreign_key="agendapunten.id")
    
    omschrijving: Optional[str] = None
    volgnummer: Optional[str] = None
    tussenkop: Optional[str] = None
    overig: Optional[str] = None
    
    starttijd: Optional[datetime] = None
    eindtijd: Optional[datetime] = None
    locatie: Optional[str] = None
    
    geplandvolgnummer: Optional[str] = None
    geplandeeindtijd: Optional[datetime] = None
    geplandestarttijd: Optional[datetime] = None
    
    indicatiehamerstuk: Optional[bool] = None
    indicatiebehandeld: Optional[bool] = None
    indicatiebesloten: Optional[bool] = None
    
    # Relationships
    vergadering: Optional["VergaderingDB"] = Relationship(back_populates="agendapunten")
    hoofdagendapunt: Optional["AgendapuntDB"] = Relationship(
        back_populates="subagendapunten",
        sa_relationship_kwargs={"remote_side": "AgendapuntDB.id"}
    )
    subagendapunten: List["AgendapuntDB"] = Relationship(back_populates="hoofdagendapunt")


class InformatieObjectDB(SQLModel, table=True):
    """Informatieobject database model"""
    __tablename__ = "informatieobjecten"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    pid: str = Field(index=True, unique=True)
    pid_uuid: Optional[str] = Field(default=None, index=True)
    webpaginalink: str
    
    # Organisatie fields
    organisatie_type: str
    organisatie_code: str
    organisatie_naam: str
    
    titel: str
    wooinformatiecategorie: str
    datumingediend: date
    
    external_id: Optional[str] = None
    auteur: Optional[str] = None
    bronorganisatie: Optional[str] = None
    creatiedatum: Optional[str] = None
    informatieobjecttype: Optional[str] = None
    formaat: Optional[str] = None
    omschrijving: Optional[str] = None
    taal: Optional[str] = None
    
    # Gerelateerd informatieobject
    gerelateerd_informatieobject_id: Optional[str] = None
    gerelateerd_rol: Optional[str] = None


class VergaderingDB(SQLModel, table=True):
    """Vergadering database model"""
    __tablename__ = "vergaderingen"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    pid: str = Field(index=True, unique=True)
    pid_uuid: Optional[str] = Field(default=None, index=True)
    webpaginalink: Optional[str] = None
    
    # Organisatie fields
    organisatie_type: str
    organisatie_code: str
    organisatie_naam: str
    
    dossiertype: str
    naam: str
    
    aanvang: Optional[datetime] = None
    einde: Optional[datetime] = None
    hoofdvergadering_id: Optional[int] = Field(default=None, foreign_key="vergaderingen.id")
    
    # Gremium fields
    gremium_identificatie: Optional[str] = None
    gremium_naam: Optional[str] = None
    
    geplandeaanvang: Optional[datetime] = None
    geplandeeinde: Optional[datetime] = None
    geplandedatum: Optional[date] = None
    locatie: Optional[str] = None
    vergaderstatus: Optional[str] = None
    vergadertoelichting: Optional[str] = None
    vergaderdatum: Optional[date] = None
    vergaderingstype: Optional[str] = None
    
    # Relationships
    agendapunten: List["AgendapuntDB"] = Relationship(back_populates="vergadering")
    hoofdvergadering: Optional["VergaderingDB"] = Relationship(
        back_populates="deelvergaderingen",
        sa_relationship_kwargs={"remote_side": "VergaderingDB.id"}
    )
    deelvergaderingen: List["VergaderingDB"] = Relationship(back_populates="hoofdvergadering")
