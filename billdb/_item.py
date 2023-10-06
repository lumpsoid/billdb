from typing import Union

class Item:
    def __init__(
            self,
            photo_path: Union[str, None] = None,
            name: Union[str, None] = None,
            price: Union[float, None] = None,
            price_one: Union[int, None] = None,
            quantity: Union[int, None] = None
    ):
        self.photo_path = photo_path
        self.name = name
        self.price = price
        self.price_one = price_one
        self.quantity = quantity


    def __repr__(self):
        # params = vars(self)
        params = f'name: {self.name}\nprice: {self.price}\nprice_one: {self.price_one}\nquantity: {self.quantity}\nphoto_path: {self.photo_path}'
        return params


    def fill_defaults(self) -> object:
        if self.photo_path is None:
            self.photo_path = ''
        if self.name is None:
            self.name = ''
        if self.price is None:
            self.price = 0
        if self.price_one is None:
            self.price_one = 0
        if self.quantity is None:
            self.quantity = 1
        return self
