from app.schemas.portfolio import BrokerName


class BrokerFactory:
    @staticmethod
    def get_broker(broker_name: str):
        from app.services.broker.zerodha_broker import ZerodhaBroker
        from app.services.broker.upstox_broker import UpstoxBroker
        from app.services.broker.angelone_broker import AngelOneBroker
        from app.services.broker.groww_broker import GrowwBroker

        brokers = {
            BrokerName.ZERODHA: ZerodhaBroker,
            BrokerName.UPSTOX: UpstoxBroker,
            BrokerName.ANGEL_ONE: AngelOneBroker,
            BrokerName.GROWW: GrowwBroker,
        }
        klass = brokers.get(broker_name)
        if not klass:
            raise ValueError(f"Unsupported broker: {broker_name}")
        return klass()
