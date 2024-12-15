# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter.adapter import ItemAdapter
from scrapy.pipelines.files import FilesPipeline
from scrapy.http.request import Request
from scrapy.exceptions import DropItem

class AllaboutbirdPipeline(FilesPipeline):
  
  
  def get_media_requests(self, item, info):
    for file_url in item['img']:
      yield Request(file_url['url'])
    for file_url in item['sound']:
      yield Request(file_url)
    yield Request(item['migration-img'])
  
  def file_path(self, request: Request, response = None, info = None, *, item= None) -> str:
    split = request.url.split('/')
    if split[-2] == "mp4":
      return "video/"+split[-3]+".mp4"
    elif split[-1] == "1200":
      return "image/"+split[-2]+".jpg"
    elif split[-2] == "sound":
      return "sound/"+split[-1]
    else:
      return "image/"+split[-1] 

  def item_completed(self, results, item, info):
    file_paths = [x['path'] for ok, x in results if ok]
    if not file_paths:
      raise DropItem("Item contains no files")
    for i in range(len(item['img'])):
      item['img'][i]['location'] = file_paths[i]
    item['sound-loc'] = file_paths[len(item['img']):len(item['img'])
      +len(item['sound'])]
    item["migration-img-loc"] = file_paths[-1]
    return item
    

  

  