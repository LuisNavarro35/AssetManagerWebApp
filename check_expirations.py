from datetime import datetime, timedelta, date
from main import app, db, Asset, Maintenance, update_asset_status
from flask_login import current_user

with app.app_context():
    today = date.today()
    one_month_later = today + timedelta(days=30)

    assets = Asset.query.filter(Asset.expiration_date != None).all()

    for asset in assets:
        exp_date = asset.expiration_date
        if not exp_date:
            continue

        events = Maintenance.query.filter_by(parent_asset=asset).all()

        has_bad_event = any(
            "expired" in e.event_description.lower() and e.op_status.lower() == "bad"
            for e in events
        )
        if has_bad_event:
            continue  # Skip asset already marked as expired

        has_warning_event = any(
            "about to expire" in e.event_description.lower() and e.op_status.lower() == "warning"
            for e in events
        )

        if exp_date < today:
            # Asset expired - create a new "bad" event
            new_maintenance_event = Maintenance(
                sn=asset.sn,
                name=asset.name,
                date=today.strftime('%Y-%m-%d'),
                event_description="Asset is expired",
                user="System",  # or current_user.username if available
                op_status="Bad",
                parent_asset=asset
            )
            db.session.add(new_maintenance_event)
            db.session.commit()
            update_asset_status(asset.sn)

        elif today <= exp_date <= one_month_later:
            if not has_warning_event:
                # Asset about to expire - create warning event
                new_maintenance_event = Maintenance(
                    sn=asset.sn,
                    name=asset.name,
                    date=today.strftime('%Y-%m-%d'),
                    event_description="Asset is about to expire",
                    user="System",
                    op_status="Warning",
                    parent_asset=asset
                )
                db.session.add(new_maintenance_event)
                db.session.commit()
                update_asset_status(asset.sn)


    print("Maintenance events updated based on expiration dates.")
