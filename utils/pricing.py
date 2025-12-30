from models import PriceItem

def get_price_or_fail(service: str, provider_code: str) -> PriceItem | None:
    return PriceItem.query.filter_by(
        service=service,
        provider_code=provider_code,
        is_active=True
    ).first()
