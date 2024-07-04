from app.configuration import get_url_utm

# db = Database('postgres')
base_url: str = get_url_utm()

TYPE_ACTS = ('WayBillAct_v4', 'QueryRejectRepProduced', 'ReplyForm1',)
TYPE_PRODUCT_ACTS = ('ReplyAP', 'ReplyAP_v2', 'ReplyAP_v3',
                     'ReplySSP', 'ReplySSP_v2',
                     'ReplySpirit', 'ReplySpirit_v2')

PAUSE_BEFORE_DEL_SECCONDS = 1200
