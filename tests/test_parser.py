from json import JSONDecodeError
import pytest
from billdb._parsers._serbia import xpath_data, get_dom, get_bill_buy_date, get_bill_info, get_bill_items, get_bill_name, get_bill_price, get_bill_text

class TestSerbianParserWithNormal:
  url = "https://suf.purs.gov.rs:443/v/?vl=A1U2RVVRSDhUVTZFVVFIOFSmvAQAJ7oEAMRvQQMAAAAAAAABi8nEtiwAAACJEXBZdZJy/NmApRiEns0Sgulz4SpsZpL0dvJtAbJh7IOyoE6pEx+1qDfy59VX5fVpHsJwdGLNUg1a0R/y4+mVo85QwP7TNH4N/yzwrv6nrn1/m+rApP1xaGvy8K11wId0HqIuNIWi5XYQa3ah7fJ+LDi2Hyi/o5/SqDCYN58Hz2VnD4uTg+kmhnTSV6YjFtFRykSBoXx7mKh4SEj352l7r076EAtrrJmdqWFYpcY6qYCzxvwXicNpFnZOHrkuvxYqw86ktSB/nvTRvVGNDPkFmCEMe73K6NArhrajz0pPjsHECoT5FcX1ziqxwRPsv4k0ef1leofQ3djA+Wi3/dIrFixHLL7GbFV1l4r8giajLYOxBEdx0px1MIXuyperIu2OEJrjCiK5QpciFq1Payd1vggQnD7ccsbDXfNuG6r9JekuZvF6XGpgGqL+c9duSOpdW0Rrr+SX1RFmHLhOsFeu38HEVvSckjGaXUmC74bflQ0ggCl2fbic3tWUlfKT6gy3NATDpm7/hU/D2ljOJgu87bP6r7evdhLse9fnUn4DLwVioi32xKnOopaEVQZ508DgNEPCVOppgSXM93cHUOA2HGqzgFL+bR+cV4PmPdgeHWvPpyoHb9QPJZwUZcTHm3v17dR/5gbeKeLoMiSsfXsDrYfl9oYdF6Ml+p4pbyouh7T2pV3zexxL8OWcOlfoGJs="
  dom = get_dom(url)

  def test_get_bill_info(self):
    info = get_bill_info(self.url)
    assert info[0] == "1002298-177 - Maxi"
    assert info[1] == "2023-11-13"
    assert info[2] == 5462.01 
    assert info[3] == "rsd"
    assert info[4] == "serbia"
    assert len(info[5].split('\n')) == 59
    assert len(info[6]) == 16


  def test_get_bill_buy_date(self):
    date = get_bill_buy_date(self.dom, xpath_data["buy_date_xpath"], "%d.%m.%Y.", "%Y-%m-%d")
    assert date == "2023-11-13"


  def test_get_bill_items(self):
    items = get_bill_items(self.dom, xpath_data["token_xpath"], xpath_data["token_search"], xpath_data["invoce_xpath"])
    assert len(items) == 16

  def test_get_bill_name(self):
    name = get_bill_name(self.dom, xpath_data["name_xpath"])
    assert name == "1002298-177 - Maxi"


  def test_get_bill_price(self):
    price = get_bill_price(self.dom, xpath_data["price_xpath"])
    assert price == 5462.01 


  def test_get_bill_text(self):
    bill_text = get_bill_text(self.dom, xpath_data["bill_xpath"])
    assert len(bill_text.split('\n')) == 59

class TestSerbianParserWithCopy:
  url = "https://suf.purs.gov.rs/v/?vl=A0tCNk5ZQ0FRVDg0WEwyTzD%2FbAAARQgAAGBV7AMAAAAAAAABi02%2BdwkCAABGlRNCZvaa5T6pTJsamBVo3NEkwM3yboEA0h4Kxc5t%2F42RN0V%2B6evWH8fWx0o4nvpqSb%2B%2FEo70p5DYU%2BUzjYHJFMJwwy%2B1EF9ePYIu6mjtGGjv%2BgP8ZDXj%2BO4mqqJavL0BLizdY6ixBxPTC3tZx0y3U4%2BUNDDQ6VtLigni86w5iwRs%2F8hpwt5DoEdqqQp8dQDf4CLe6F5KeDsGHYsvXRwyqWJ22FVimmUneK%2B92pyTKNPsdQJ1tgbBeLRvYog5Mfx2V2dK4Cbb0YPWESXZ146plM1%2B2YfgUaItZTsinp0dd%2BU4x9j%2BOfdYy0C0VP46WNfna5QvSzyep6PBjTRM6kbRjEZCKuMrcrjENRUaTc7Nd%2BdQ60zjpDQT4Qtg7UcJnN3hItkEj7CFyZlaYb7pEJ66gsMtmcKMyjIvEIHjPDHw55nDzig9dSfZalHkGx%2BgFZfXCnDRsvlBWoiPT5MIdP0J5PeEgVvlRtvPXAqxX%2BfNpWyx6lDG0x2PeMvubPHpzCO0mhGsTUq9fTJaxdldg8I33BalRBRLm96AmCqtaB6Eca5wpkvgsIsNpi7EkE1eGyEY1G8Bf5fDlzOlO%2FUNmhyhmnSen9HBwY9TVR2z9%2Bb7c8G3wQhu0DXvGIgfdDyKfEmVYRtaCeDHrh65Wz2pcASI%2B%2FPZpftE38fl5WNLwUsHFYApFv6tSZ8R2AEqYoi9rNg%3D"
  dom = get_dom(url)

  def test_get_bill_info(self):
    with pytest.raises(JSONDecodeError):
      info = get_bill_info(self.url)

  def test_get_bill_buy_date(self):
    date = get_bill_buy_date(self.dom, xpath_data["buy_date_xpath"], "%d.%m.%Y.", "%Y-%m-%d")
    assert date == "2023-10-20"


  def test_get_bill_items(self):
    with pytest.raises(JSONDecodeError):
      items = get_bill_items(self.dom, xpath_data["token_xpath"], xpath_data["token_search"], xpath_data["invoce_xpath"])

  def test_get_bill_name(self):
    name = get_bill_name(self.dom, xpath_data["name_xpath"])
    assert name == "1202661-IKEA Srbija d.o.o. Prodavnica IKEA Beograd istok"


  def test_get_bill_price(self):
    price = get_bill_price(self.dom, xpath_data["price_xpath"])
    assert price == 6582.00


  def test_get_bill_text(self):
    bill_text = get_bill_text(self.dom, xpath_data["bill_xpath"])
    assert len(bill_text.split('\n')) == 43