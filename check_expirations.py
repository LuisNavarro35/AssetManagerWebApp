from datetime import datetime, timedelta, date
from main import app, db, Asset, Maintenance, update_asset_status

with app.app_context():
    today = date.today()
    one_month_later = today + timedelta(days=30)

    assets = Asset.query.filter(Asset.expiration_date != None).all()

    for asset in assets:
        exp_date = asset.expiration_date
        if not exp_date:
            continue

        # Fetch all maintenance events related to expiration
        events = Maintenance.query.filter_by(parent_asset=asset).all()

        has_bad_event = None
        has_warning_event = None

        for e in events:
            desc = e.event_description.lower()
            status = e.op_status.lower()
            if "expired" in desc and status == "bad":
                has_bad_event = e
            elif "about to expire" in desc and status == "warning":
                has_warning_event = e

        # ✅ CASE 1: Asset expiration date now GOOD — remove warning/bad
        if exp_date > one_month_later:
            for event in [has_bad_event, has_warning_event]:
                if event:
                    event.op_status = "Repaired"
                    event.event_description = "Asset expiration resolved"
                    event.date = today.strftime('%Y-%m-%d')
                    event.user = "System"
                    db.session.add(event)
                    db.session.commit()
                    update_asset_status(asset.sn)
            continue  # Skip rest since asset is no longer close to expiring

        # ✅ CASE 2: Expired asset → create "bad" event (only if not exists)
        if exp_date < today:
            if not has_bad_event:
                new_maintenance_event = Maintenance(
                    sn=asset.sn,
                    name=asset.name,
                    date=today.strftime('%Y-%m-%d'),
                    event_description="Asset is expired",
                    user="System",
                    op_status="Bad",
                    parent_asset=asset
                )
                db.session.add(new_maintenance_event)
                db.session.commit()
                update_asset_status(asset.sn)

        # ✅ CASE 3: Asset expiring soon → create "warning" event
        elif today <= exp_date <= one_month_later:
            if not has_warning_event:
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

    print("Asset expiration check completed.")

