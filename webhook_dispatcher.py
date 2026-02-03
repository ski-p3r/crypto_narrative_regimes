import os
from dotenv import load_dotenv
load_dotenv()
import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict, List
import requests
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("webhook_dispatcher")


@dataclass
class WebhookEvent:
    """Represents an event to be sent via webhook."""
    event_type: str
    timestamp: datetime
    symbol: str
    severity: str  # "INFO", "WARNING", "CRITICAL"
    title: str
    description: str
    data: Dict[str, Any]
    source: str  # "CASCADE", "FUNDING", "VOLATILITY", "CORRELATION", etc.


class WebhookDispatcher:
    """
    Dispatch events to registered webhook endpoints.
    Supports multiple webhook registrations per event type.
    """
    
    def __init__(self):
        self.webhooks = self._load_webhook_config()
        self.event_queue = []
    
    def _load_webhook_config(self) -> Dict[str, List[str]]:
        """
        Load webhook URLs from environment.
        Format: WEBHOOKS_REGIME_CHANGE=https://webhook.com/regime,...
        """
        webhooks = {}
        
        webhook_env_vars = [
            ("WEBHOOKS_CASCADE", "CASCADE"),
            ("WEBHOOKS_FUNDING", "FUNDING"),
            ("WEBHOOKS_VOLATILITY", "VOLATILITY"),
            ("WEBHOOKS_CORRELATION", "CORRELATION"),
            ("WEBHOOKS_REGIME", "REGIME"),
            ("WEBHOOKS_ALL", "ALL"),
        ]
        
        for env_var, event_type in webhook_env_vars:
            urls = os.getenv(env_var, "").strip()
            if urls:
                webhooks[event_type] = [url.strip() for url in urls.split(",") if url.strip()]
                log.info(f"[WEBHOOK] Loaded {len(webhooks[event_type])} webhooks for {event_type}")
        
        return webhooks
    
    def register_webhook(self, event_type: str, url: str):
        """Dynamically register a new webhook."""
        if event_type not in self.webhooks:
            self.webhooks[event_type] = []
        
        if url not in self.webhooks[event_type]:
            self.webhooks[event_type].append(url)
            log.info(f"[WEBHOOK] Registered webhook for {event_type}: {url}")
    
    def dispatch_event(self, event: WebhookEvent) -> bool:
        """
        Dispatch an event to all registered webhooks.
        Returns True if at least one webhook succeeded.
        """
        target_webhooks = []
        
        # Collect target webhooks
        event_source = event.source
        if event_source in self.webhooks:
            target_webhooks.extend(self.webhooks[event_source])
        
        # Always send to generic "ALL" webhooks
        if "ALL" in self.webhooks:
            target_webhooks.extend(self.webhooks["ALL"])
        
        if not target_webhooks:
            log.debug(f"[WEBHOOK] No webhooks registered for {event.source}")
            return False
        
        # Prepare payload
        payload = {
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "symbol": event.symbol,
            "severity": event.severity,
            "title": event.title,
            "description": event.description,
            "source": event.source,
            "data": event.data,
        }
        
        success_count = 0
        
        for url in set(target_webhooks):  # Deduplicate
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=5,
                    headers={"Content-Type": "application/json"},
                )
                
                if response.status_code < 300:
                    success_count += 1
                    log.info(f"[WEBHOOK] Successfully sent {event.event_type} to {url}")
                else:
                    log.warning(f"[WEBHOOK] Failed to send to {url}: {response.status_code}")
            
            except requests.Timeout:
                log.warning(f"[WEBHOOK] Timeout sending to {url}")
            except Exception as e:
                log.error(f"[WEBHOOK] Error sending to {url}: {e}")
        
        return success_count > 0
    
    def dispatch_cascade_event(self, symbol: str, event_data: Dict[str, Any]):
        """Send liquidation cascade alert."""
        event = WebhookEvent(
            event_type="LIQUIDATION_CASCADE",
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            severity="CRITICAL" if event_data.get('severity', 0) > 2 else "WARNING",
            title=f"Liquidation Cascade Detected - {symbol}",
            description=f"Large liquidation event with velocity {event_data.get('velocity_usd_per_hour', 0):.0f} USD/h",
            data=event_data,
            source="CASCADE",
        )
        return self.dispatch_event(event)
    
    def dispatch_funding_anomaly(self, symbol: str, event_data: Dict[str, Any]):
        """Send funding rate anomaly alert."""
        event = WebhookEvent(
            event_type="FUNDING_ANOMALY",
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            severity="WARNING",
            title=f"Funding Rate Anomaly - {symbol}",
            description=f"Extreme funding detected: {event_data.get('funding_rate', 0):.4f}",
            data=event_data,
            source="FUNDING",
        )
        return self.dispatch_event(event)
    
    def dispatch_reversal_signal(self, symbol: str, event_data: Dict[str, Any]):
        """Send funding reversal signal."""
        event = WebhookEvent(
            event_type="FUNDING_REVERSAL",
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            severity="INFO",
            title=f"Funding Reversal Signal - {symbol}",
            description=f"Funding trend reversal detected at level: {event_data.get('extreme_level', 'UNKNOWN')}",
            data=event_data,
            source="FUNDING",
        )
        return self.dispatch_event(event)
    
    def dispatch_volatility_regime_change(self, symbol: str, event_data: Dict[str, Any]):
        """Send volatility regime change alert."""
        old_regime = event_data.get('old_regime', 'UNKNOWN')
        new_regime = event_data.get('new_regime', 'UNKNOWN')
        
        event = WebhookEvent(
            event_type="VOLATILITY_REGIME_CHANGE",
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            severity="WARNING" if new_regime in ["HIGH_VOL", "EXPLOSIVE"] else "INFO",
            title=f"Volatility Regime Change - {symbol}",
            description=f"Volatility changed from {old_regime} to {new_regime}",
            data=event_data,
            source="VOLATILITY",
        )
        return self.dispatch_event(event)
    
    def dispatch_correlation_break(self, asset_pair: str, event_data: Dict[str, Any]):
        """Send correlation break alert."""
        event = WebhookEvent(
            event_type="CORRELATION_BREAK",
            timestamp=datetime.now(timezone.utc),
            symbol=asset_pair.split("/")[0],  # Use first asset as symbol
            severity="WARNING",
            title=f"Correlation Break - {asset_pair}",
            description=f"Pair correlation dropped to {event_data.get('return_correlation', 0):.2f}",
            data=event_data,
            source="CORRELATION",
        )
        return self.dispatch_event(event)
    
    def dispatch_regime_confirmation(self, symbol: str, event_data: Dict[str, Any]):
        """Send regime confirmation (positive signal)."""
        event = WebhookEvent(
            event_type="REGIME_CONFIRMED",
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            severity="INFO",
            title=f"Regime Confirmed - {symbol}",
            description=f"Multi-timeframe confirmation for {event_data.get('primary_regime', 'UNKNOWN')} regime",
            data=event_data,
            source="REGIME",
        )
        return self.dispatch_event(event)
    
    def dispatch_batch_events(self, events: List[WebhookEvent]) -> Dict[str, int]:
        """Dispatch multiple events and return summary."""
        summary = {
            "total_events": len(events),
            "successful": 0,
            "failed": 0,
        }
        
        for event in events:
            if self.dispatch_event(event):
                summary["successful"] += 1
            else:
                summary["failed"] += 1
        
        log.info(f"[WEBHOOK] Batch dispatch summary: {summary}")
        return summary


# Global dispatcher instance
_dispatcher = None


def get_dispatcher() -> WebhookDispatcher:
    """Get or create global dispatcher instance."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = WebhookDispatcher()
    return _dispatcher


def send_event(event: WebhookEvent) -> bool:
    """Convenience function to send an event."""
    dispatcher = get_dispatcher()
    return dispatcher.dispatch_event(event)


if __name__ == "__main__":
    # Test webhook dispatcher
    dispatcher = WebhookDispatcher()
    
    # Example event
    test_event = WebhookEvent(
        event_type="TEST_EVENT",
        timestamp=datetime.now(timezone.utc),
        symbol="BTC/USDT",
        severity="INFO",
        title="Test Webhook Event",
        description="This is a test event from the webhook dispatcher",
        data={"test": True, "value": 12345},
        source="TEST",
    )
    
    print(f"Registered webhooks: {dispatcher.webhooks}")
    
    # Would need actual webhooks configured to test
    # result = dispatcher.dispatch_event(test_event)
    # print(f"Dispatch result: {result}")
