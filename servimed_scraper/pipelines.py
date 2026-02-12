class CollectOrderResultPipeline:
    """
    Pipeline que armazena o resultado do pedido (codigo_confirmacao, status)
    em uma lista passada via settings['ORDER_RESULT_CONTAINER'].
    Usado pelo order_runner (Nível 3).
    """
    def __init__(self, result_container):
        self.result_container = result_container

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            result_container=crawler.settings.get("ORDER_RESULT_CONTAINER", []),
        )

    def process_item(self, item, spider):
        if hasattr(item, "get") and item.get("codigo_confirmacao") and item.get("status"):
            self.result_container.append(dict(item))
        return item


class CollectItemsPipeline:
    """
    Pipeline que armazena os itens em uma lista (para uso pelo worker).
    A lista é passada via settings['COLLECT_ITEMS_LIST'].
    """
    def __init__(self, items_list):
        self.items_list = items_list

    @classmethod
    def from_crawler(cls, crawler):
        return cls(items_list=crawler.settings.get("COLLECT_ITEMS_LIST", []))

    def process_item(self, item, spider):
        self.items_list.append(dict(item))
        return item
