class NotificationProvider:
    code: str = ""

    def send(self, notification, *, title: str, body: str) -> None:
        raise NotImplementedError
