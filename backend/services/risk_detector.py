"""
Financial Risk Detection AI
Analyzes transactions for potential risks and generates alerts
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import json
from backend.models import TransactionEntry
from backend.services.duplicate_detector import DuplicateDetector

class RiskDetector:
    def __init__(self):
        self.duplicate_detector = DuplicateDetector()

    def analyze_transactions(self, transactions: List[TransactionEntry]) -> Dict[str, Any]:
        """
        Analyze a list of transactions and generate risk alerts

        Args:
            transactions: List of TransactionEntry objects

        Returns:
            Dict with alerts or no_alerts flag
        """
        alerts = []

        if not transactions:
            return {"alerts": [], "no_alerts": True}

        # Convert to dicts for easier processing
        transaction_dicts = [t.dict() for t in transactions]

        # Rule 1: Duplicate charges
        alerts.extend(self._detect_duplicates(transaction_dicts))

        # Rule 2: Unusually large transactions
        alerts.extend(self._detect_large_transactions(transaction_dicts))

        # Rule 3: Low confidence fields
        alerts.extend(self._detect_low_confidence(transaction_dicts))

        # Rule 4: Sudden monthly category changes
        alerts.extend(self._detect_category_changes(transaction_dicts))

        # Rule 5: Subscription/recurring payments
        alerts.extend(self._detect_subscriptions(transaction_dicts))

        # Rule 6: Projected balance risk
        alerts.extend(self._detect_balance_risk(transaction_dicts))

        # Rule 7: First-time vendor with high value
        alerts.extend(self._detect_first_time_vendor(transaction_dicts))

        # Rule 8: Spending spikes on weekends/holidays
        alerts.extend(self._detect_weekend_spikes(transaction_dicts))

        # Rule 9: Potential tax-deductible expenses
        alerts.extend(self._detect_tax_deductible(transaction_dicts))

        if not alerts:
            return {"alerts": [], "no_alerts": True}

        return {"alerts": alerts}

    def _detect_duplicates(self, transactions: List[Dict]) -> List[Dict]:
        alerts = []
        processed = set()

        for i, tx in enumerate(transactions):
            if tx['id'] in processed:
                continue

            duplicates = self.duplicate_detector.find_duplicates(tx, transactions[:i] + transactions[i+1:], threshold=90)
            if duplicates:
                dup_ids = [dup['entry_id'] for dup in duplicates] + [tx['id']]
                alerts.append({
                    "severity": "medium",
                    "type": "duplicate_charges",
                    "message": f"Potential duplicate transactions detected for {tx['vendor']} with amount {tx['amount']}",
                    "transaction_ids": dup_ids,
                    "recommended_action": "Review and merge duplicate transactions"
                })
                processed.update(dup_ids)

        return alerts

    def _detect_large_transactions(self, transactions: List[Dict]) -> List[Dict]:
        alerts = []
        amounts = [tx['amount'] for tx in transactions if tx['amount'] > 0]
        if not amounts:
            return alerts

        avg_amount = sum(amounts) / len(amounts)
        threshold = avg_amount * 2  # Unusually large if > 2x average

        for tx in transactions:
            if tx['amount'] > threshold:
                alerts.append({
                    "severity": "high",
                    "type": "unusually_large_transaction",
                    "message": f"Transaction amount {tx['amount']} is unusually large compared to historical average of {avg_amount:.2f}",
                    "transaction_ids": [tx['id']],
                    "recommended_action": "Verify the transaction details and source"
                })

        return alerts

    def _detect_low_confidence(self, transactions: List[Dict]) -> List[Dict]:
        alerts = []
        for tx in transactions:
            low_fields = []
            conf = tx['confidence']
            if conf['vendor'] < 0.9:
                low_fields.append('vendor')
            if conf['amount'] < 0.9:
                low_fields.append('amount')
            if conf['date'] < 0.9:
                low_fields.append('date')
            if conf['category'] < 0.9:
                low_fields.append('category')

            if low_fields:
                alerts.append({
                    "severity": "medium",
                    "type": "low_confidence_fields",
                    "message": f"Low confidence in fields: {', '.join(low_fields)} for transaction {tx['id']}",
                    "transaction_ids": [tx['id']],
                    "recommended_action": "Review and correct the low-confidence fields"
                })

        return alerts

    def _detect_category_changes(self, transactions: List[Dict]) -> List[Dict]:
        alerts = []
        monthly_spend = defaultdict(lambda: defaultdict(float))

        for tx in transactions:
            try:
                date = datetime.strptime(tx['date'], "%Y-%m-%d")
                month_key = f"{date.year}-{date.month:02d}"
                monthly_spend[month_key][tx['category']] += tx['amount']
            except:
                continue

        # Check for changes > 25% between consecutive months
        months = sorted(monthly_spend.keys())
        for i in range(1, len(months)):
            prev_month = monthly_spend[months[i-1]]
            curr_month = monthly_spend[months[i]]

            for cat in set(prev_month.keys()) | set(curr_month.keys()):
                prev_amt = prev_month.get(cat, 0)
                curr_amt = curr_month.get(cat, 0)

                if prev_amt > 0:
                    change_pct = ((curr_amt - prev_amt) / prev_amt) * 100
                    if abs(change_pct) > 25:
                        # Find transaction IDs for this category in current month
                        tx_ids = [tx['id'] for tx in transactions if tx.get('category') == cat and tx['date'].startswith(months[i])]
                        if tx_ids:
                            alerts.append({
                                "severity": "medium",
                                "type": "sudden_category_change",
                                "message": f"Sudden {change_pct:.1f}% change in {cat} spending from {prev_amt:.2f} to {curr_amt:.2f} in {months[i]}",
                                "transaction_ids": tx_ids,
                                "recommended_action": "Investigate the reason for the spending change"
                            })

        return alerts

    def _detect_subscriptions(self, transactions: List[Dict]) -> List[Dict]:
        alerts = []
        vendor_groups = defaultdict(list)

        for tx in transactions:
            vendor_groups[tx['vendor']].append(tx)

        for vendor, txs in vendor_groups.items():
            if len(txs) < 3:
                continue

            # Check for recurring amounts
            amounts = [tx['amount'] for tx in txs]
            if len(set(amounts)) == 1:  # All same amount
                dates = sorted([datetime.strptime(tx['date'], "%Y-%m-%d") for tx in txs])
                intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
                avg_interval = sum(intervals) / len(intervals)

                if 25 <= avg_interval <= 35:  # Monthly
                    tx_ids = [tx['id'] for tx in txs]
                    alerts.append({
                        "severity": "low",
                        "type": "subscription_detected",
                        "message": f"Potential monthly subscription detected for {vendor} with amount {amounts[0]}",
                        "transaction_ids": tx_ids,
                        "recommended_action": "Confirm if this is a subscription and categorize accordingly"
                    })

        return alerts

    def _detect_balance_risk(self, transactions: List[Dict]) -> List[Dict]:
        alerts = []
        # Assume starting balance is the first remaining_balance or 0
        sorted_txs = sorted(transactions, key=lambda x: x['date'])
        balance = sorted_txs[0].get('remaining_balance', 0) if sorted_txs else 0

        projected_dates = []
        current_date = datetime.now()

        for tx in sorted_txs:
            try:
                tx_date = datetime.strptime(tx['date'], "%Y-%m-%d")
                if tx_date > current_date:
                    projected_dates.append((tx_date, tx['amount'] if tx['transaction_type'] == 'expense' else -tx['amount']))
            except:
                continue

        # Project balance over next 90 days
        future_balance = balance
        depletion_date = None

        for date, amount in projected_dates:
            future_balance -= amount
            if future_balance < 0 and depletion_date is None:
                depletion_date = date
                break

        if depletion_date and (depletion_date - current_date).days <= 90:
            days = (depletion_date - current_date).days
            alerts.append({
                "severity": "high",
                "type": "projected_balance_risk",
                "message": f"Projected cash depletion within {days} days based on upcoming expenses",
                "transaction_ids": [],  # All future transactions
                "recommended_action": "Review upcoming expenses and adjust budget"
            })

        return alerts

    def _detect_first_time_vendor(self, transactions: List[Dict]) -> List[Dict]:
        alerts = []
        vendor_counts = defaultdict(int)
        vendor_amounts = defaultdict(float)

        for tx in transactions:
            vendor_counts[tx['vendor']] += 1
            vendor_amounts[tx['vendor']] += tx['amount']

        avg_amount = sum(tx['amount'] for tx in transactions) / len(transactions) if transactions else 0

        for vendor, count in vendor_counts.items():
            if count == 1 and vendor_amounts[vendor] > avg_amount * 1.5:
                tx_id = next(tx['id'] for tx in transactions if tx['vendor'] == vendor)
                alerts.append({
                    "severity": "medium",
                    "type": "first_time_high_value_vendor",
                    "message": f"First-time vendor {vendor} with high value transaction of {vendor_amounts[vendor]}",
                    "transaction_ids": [tx_id],
                    "recommended_action": "Verify the legitimacy of this new vendor transaction"
                })

        return alerts

    def _detect_weekend_spikes(self, transactions: List[Dict]) -> List[Dict]:
        alerts = []
        weekday_spend = 0
        weekend_spend = 0
        weekday_count = 0
        weekend_count = 0

        for tx in transactions:
            try:
                date = datetime.strptime(tx['date'], "%Y-%m-%d")
                if date.weekday() >= 5:  # Saturday=5, Sunday=6
                    weekend_spend += tx['amount']
                    weekend_count += 1
                else:
                    weekday_spend += tx['amount']
                    weekday_count += 1
            except:
                continue

        if weekday_count > 0 and weekend_count > 0:
            avg_weekday = weekday_spend / weekday_count
            avg_weekend = weekend_spend / weekend_count

            if avg_weekend > avg_weekday * 1.5:
                weekend_tx_ids = [tx['id'] for tx in transactions if datetime.strptime(tx['date'], "%Y-%m-%d").weekday() >= 5]
                alerts.append({
                    "severity": "low",
                    "type": "weekend_spending_spike",
                    "message": f"Unusual spending spike on weekends: {avg_weekend:.2f} vs weekday average {avg_weekday:.2f}",
                    "transaction_ids": weekend_tx_ids,
                    "recommended_action": "Review weekend transactions for unusual activity"
                })

        return alerts

    def _detect_tax_deductible(self, transactions: List[Dict]) -> List[Dict]:
        alerts = []
        tax_categories = ['business', 'medical', 'charity', 'education', 'home_office']

        for tx in transactions:
            if tx['category'].lower() in tax_categories and tx['amount'] > 100:  # Arbitrary threshold
                alerts.append({
                    "severity": "low",
                    "type": "potential_tax_deductible",
                    "message": f"Potential tax-deductible expense in category {tx['category']} for amount {tx['amount']}",
                    "transaction_ids": [tx['id']],
                    "recommended_action": "Check if this expense qualifies for tax deduction"
                })

        return alerts
