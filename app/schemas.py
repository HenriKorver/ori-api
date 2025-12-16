from typing import Optional, List, Union
from datetime import datetime, date
from pydantic import BaseModel, Field


# Organisatie schemas
class Gemeente(BaseModel):
    gemeente: str = Field(..., example="gm0363")
    naam: str = Field(..., example="Gemeente Amsterdam")


class Provincie(BaseModel):
    provincie: str = Field(..., example="pv27")
    naam: str = Field(..., example="Provincie Groningen")


class Waterschap(BaseModel):
    waterschap: str = Field(..., example="ws0654")
    naam: str = Field(..., example="Waterschap Aa en Maas")


Organisatie = Union[Gemeente, Provincie, Waterschap]


# Gremium schema
class Gremium(BaseModel):
    gremiumidentificatie: str
    gremiumnaam: str


# Verwijzing naar resource
class VerwijzingNaarResource(BaseModel):
    id: str
    url: Optional[str] = None


# Gerelateerd informatieobject
class GerelateerdInformatieobject(BaseModel):
    informatieobject: str
    rol: str


# Agendapunt schemas
class AgendapuntBase(BaseModel):
    webpaginalink: Optional[str] = None
    organisatie: Organisatie
    dossiertype: str = Field(..., example="agendapunt")
    agendapuntnaam: str
    vergadering: VerwijzingNaarResource
    hoofdagendapunt: Optional[VerwijzingNaarResource] = None
    omschrijving: Optional[str] = None
    volgnummer: Optional[str] = None
    subagendapunten: Optional[List[str]] = None
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


class AgendapuntZonderPid(AgendapuntBase):
    pass


class Agendapunt(AgendapuntBase):
    pid: str


# Informatieobject schemas
class InformatieObjectBase(BaseModel):
    webpaginalink: str = Field(..., example="https://example.com/mijn-pagina.html")
    organisatie: Organisatie
    titel: str
    wooinformatiecategorie: str = Field(..., example="c_db4862c3")
    datumingediend: date = Field(..., example="2017-02-09")
    id: Optional[str] = None
    auteur: Optional[str] = None
    bronorganisatie: Optional[str] = None
    creatiedatum: Optional[str] = None
    informatieobjecttype: Optional[str] = None
    formaat: Optional[str] = None
    omschrijving: Optional[str] = None
    taal: Optional[str] = None
    vergaderingen: Optional[List[VerwijzingNaarResource]] = None
    agendapunten: Optional[List[VerwijzingNaarResource]] = None
    gerelateerdinformatieobject: Optional[GerelateerdInformatieobject] = None


class InformatieObjectZonderPid(InformatieObjectBase):
    pass


class InformatieObject(InformatieObjectBase):
    pid: str


# Vergadering schemas
class VergaderingBase(BaseModel):
    webpaginalink: Optional[str] = None
    organisatie: Organisatie
    dossiertype: str = Field(..., example="vergadering")
    naam: str = Field(..., example="Raadsvergadering")
    aanvang: Optional[datetime] = None
    hoofdvergadering: Optional[VerwijzingNaarResource] = None
    einde: Optional[datetime] = None
    georganiseerddoorgremium: Optional[Gremium] = None
    geplandeaanvang: Optional[datetime] = None
    geplandeeinde: Optional[datetime] = None
    geplandedatum: Optional[date] = None
    locatie: Optional[str] = None
    vergaderstatus: Optional[str] = None
    vergadertoelichting: Optional[str] = None
    vergaderdatum: Optional[date] = None
    vergaderingstype: Optional[str] = None
    deelvergaderingen: Optional[List[str]] = None
    agendapunten: Optional[List[str]] = None


class VergaderingZonderPid(VergaderingBase):
    pass


class Vergadering(VergaderingBase):
    pid: str


# Paginated responses
class PaginatedAgendapuntList(BaseModel):
    next: Optional[str] = None
    previous: Optional[str] = None
    results: List[Agendapunt]


class PaginatedInformatieObjectList(BaseModel):
    next: Optional[str] = None
    previous: Optional[str] = None
    results: List[InformatieObject]


class PaginatedVergaderingList(BaseModel):
    next: Optional[str] = None
    previous: Optional[str] = None
    results: List[Vergadering]


# Error response
class ErrorResponse(BaseModel):
    titel: str
    status: int
    detail: str
