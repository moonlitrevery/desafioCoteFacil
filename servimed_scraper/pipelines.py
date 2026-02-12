
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
