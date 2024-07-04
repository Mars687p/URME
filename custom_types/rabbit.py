from typing import NotRequired, Optional, TypedDict


class RabbitMessageQueueUTM(TypedDict):
    type_doc: Optional[str]
    uuid: str
    id_doc: int
    type_file: str
    xml: NotRequired[str]
