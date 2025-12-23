from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func, not_, text
from sqlalchemy.exc import IntegrityError
import logging

from src.database.models import CarAd, ScrapingLog
from src.database.session import ScopedSession

logger = logging.getLogger(__name__)


class CarAdRepository:

    def __init__(self, session: Optional[Session] = None):
        self.session = session or ScopedSession()

    def create(self, car_data: Dict[str, Any]) -> Optional[CarAd]:
        try:
            # Check if ad already exists
            existing = self.get_by_url(car_data.get("url"))
            if existing:
                logger.debug(f"Ad already exists: {car_data.get('url')}")
                return None

            # Create new ad
            car_ad = CarAd(**car_data)
            self.session.add(car_ad)
            self.session.commit()
            self.session.refresh(car_ad)
            logger.debug(f"Created new car ad: {car_ad.id}")
            return car_ad

        except IntegrityError as e:
            self.session.rollback()
            logger.warning(f"Integrity error when creating car ad: {e}")
            return None
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating car ad: {e}")
            raise

    def bulk_create(self, cars_data: List[Dict[str, Any]]) -> List[CarAd]:
        created_ads = []
        duplicates_count = 0

        for car_data in cars_data:
            try:
                # Check for duplicates by URL
                existing = (
                    self.session.query(CarAd)
                    .filter(CarAd.url == car_data.get("url"))
                    .first()
                )

                if existing:
                    duplicates_count += 1
                    continue

                # Create new ad
                car_ad = CarAd(**car_data)
                self.session.add(car_ad)
                created_ads.append(car_ad)

            except Exception as e:
                logger.warning(f"Error processing car data: {e}")
                continue

        try:
            if created_ads:
                self.session.commit()
                for ad in created_ads:
                    self.session.refresh(ad)
                logger.info(
                    f"Created {len(created_ads)} new ads, skipped {duplicates_count} duplicates"
                )
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in bulk create: {e}")
            created_ads = []

        return created_ads

    def get_by_id(self, ad_id: int) -> Optional[CarAd]:
        return self.session.query(CarAd).filter(CarAd.id == ad_id).first()

    def get_by_url(self, url: str) -> Optional[CarAd]:
        return self.session.query(CarAd).filter(CarAd.url == url).first()

    def get_by_vin(self, vin: str) -> Optional[CarAd]:
        return self.session.query(CarAd).filter(CarAd.car_vin == vin).first()

    def get_all(
        self, skip: int = 0, limit: int = 100, active_only: bool = True
    ) -> List[CarAd]:
        query = self.session.query(CarAd)

        if active_only:
            query = query.filter(CarAd.is_active == True)

        return query.order_by(desc(CarAd.created_at)).offset(skip).limit(limit).all()

    def search(
        self,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
        location: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[CarAd]:
        query = self.session.query(CarAd).filter(CarAd.is_active == True)

        if brand:
            query = query.filter(CarAd.brand.ilike(f"%{brand}%"))

        if model:
            query = query.filter(CarAd.model.ilike(f"%{model}%"))

        if min_price is not None:
            query = query.filter(CarAd.price_usd >= min_price)

        if max_price is not None:
            query = query.filter(CarAd.price_usd <= max_price)

        if min_year is not None:
            query = query.filter(CarAd.year >= min_year)

        if max_year is not None:
            query = query.filter(CarAd.year <= max_year)

        if location:
            query = query.filter(CarAd.location.ilike(f"%{location}%"))

        return query.order_by(desc(CarAd.created_at)).offset(skip).limit(limit).all()

    def update(self, ad_id: int, update_data: Dict[str, Any]) -> Optional[CarAd]:
        car_ad = self.get_by_id(ad_id)
        if not car_ad:
            return None

        try:
            for key, value in update_data.items():
                if hasattr(car_ad, key):
                    setattr(car_ad, key, value)

            self.session.commit()
            self.session.refresh(car_ad)
            return car_ad
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating car ad {ad_id}: {e}")
            return None

    def deactivate(self, ad_id: int) -> bool:
        car_ad = self.get_by_id(ad_id)
        if not car_ad:
            return False

        try:
            car_ad.is_active = False
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deactivating car ad {ad_id}: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        try:
            with self.session.connection() as conn:
                # Total count
                total_result = conn.execute(text("SELECT COUNT(*) FROM car_ads"))
                total = total_result.scalar() or 0

                # Active count
                active_result = conn.execute(
                    text("SELECT COUNT(*) FROM car_ads WHERE is_active = true")
                )
                active = active_result.scalar() or 0

                # Average price
                avg_price_result = conn.execute(
                    text(
                        "SELECT AVG(price_usd) FROM car_ads WHERE is_active = true AND price_usd > 0"
                    )
                )
                avg_price = avg_price_result.scalar() or 0

                # Average odometer
                avg_odometer_result = conn.execute(
                    text(
                        "SELECT AVG(odometer) FROM car_ads WHERE is_active = true AND odometer > 0"
                    )
                )
                avg_odometer = avg_odometer_result.scalar() or 0

                # Top brands
                brands_result = conn.execute(
                    text(
                        """
                    SELECT brand, COUNT(*) as count 
                    FROM car_ads 
                    WHERE is_active = true AND brand IS NOT NULL 
                    GROUP BY brand 
                    ORDER BY count DESC 
                    LIMIT 10
                """
                    )
                )
                brands = [{"brand": row[0], "count": row[1]} for row in brands_result]

            return {
                "total_ads": total,
                "active_ads": active,
                "avg_price": float(avg_price),
                "avg_odometer": float(avg_odometer),
                "top_brands": brands,
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
