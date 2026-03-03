import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentActiveUserDep, SessionDep
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.schemas.invoices import (
    InvoiceCreate,
    InvoicePublic,
    InvoicesPublic,
    InvoiceUpdate,
)
from app.schemas.users import Message
from app.services.customer import get_customer_by_id, normalize_image_url
from app.services.invoice import (
    create_invoice,
    delete_invoice,
    get_invoice_with_customer,
    get_invoices,
    get_latest_invoices,
    update_invoice,
)

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _to_public(invoice: Invoice, customer: Customer) -> InvoicePublic:
    return InvoicePublic(
        id=invoice.id,
        customer_id=invoice.customer_id,
        amount=str(invoice.amount),
        status=invoice.status,  # type: ignore[arg-type]
        date=invoice.date,
        name=customer.name,
        email=customer.email,
        image_url=normalize_image_url(customer.image_url, customer.email),
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
    )


@router.get("/", response_model=InvoicesPublic)
async def read_invoices(
    session: SessionDep,
    _: CurrentActiveUserDep,
    query: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
) -> InvoicesPublic:
    invoices, count = await get_invoices(session, query=query, skip=skip, limit=limit)
    return InvoicesPublic(
        data=[_to_public(invoice, customer) for invoice, customer in invoices],
        count=count,
    )


@router.get("/latest", response_model=list[InvoicePublic])
async def read_latest_invoices(
    session: SessionDep,
    _: CurrentActiveUserDep,
) -> list[InvoicePublic]:
    invoices = await get_latest_invoices(session)
    return [_to_public(invoice, customer) for invoice, customer in invoices]


@router.get("/{invoice_id}", response_model=InvoicePublic)
async def read_invoice(
    invoice_id: uuid.UUID,
    session: SessionDep,
    _: CurrentActiveUserDep,
) -> InvoicePublic:
    result = await get_invoice_with_customer(session, invoice_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
        )
    invoice, customer = result
    return _to_public(invoice, customer)


@router.post("/", response_model=InvoicePublic, status_code=status.HTTP_201_CREATED)
async def create_invoice_route(
    invoice_in: InvoiceCreate,
    session: SessionDep,
    _: CurrentActiveUserDep,
) -> InvoicePublic:
    customer = await get_customer_by_id(session, invoice_in.customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )
    invoice = await create_invoice(session, invoice_in)
    return _to_public(invoice, customer)


@router.patch("/{invoice_id}", response_model=InvoicePublic)
async def update_invoice_route(
    invoice_id: uuid.UUID,
    invoice_in: InvoiceUpdate,
    session: SessionDep,
    _: CurrentActiveUserDep,
) -> InvoicePublic:
    result = await get_invoice_with_customer(session, invoice_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
        )
    invoice, customer = result

    if invoice_in.customer_id and invoice_in.customer_id != invoice.customer_id:
        new_customer = await get_customer_by_id(session, invoice_in.customer_id)
        if not new_customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
            )
        customer = new_customer

    invoice = await update_invoice(session, invoice, invoice_in)
    return _to_public(invoice, customer)


@router.delete("/{invoice_id}", response_model=Message)
async def delete_invoice_route(
    invoice_id: uuid.UUID,
    session: SessionDep,
    _: CurrentActiveUserDep,
) -> Message:
    result = await get_invoice_with_customer(session, invoice_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
        )
    invoice, _customer = result
    await delete_invoice(session, invoice)
    return Message(message="Invoice deleted")
