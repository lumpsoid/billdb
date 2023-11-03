#include <ostream>
#include <sqlite3.h>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

class Item {
    public:
        Item(const std::string& photo_path, 
            const std::string& name,
            float price,
            float price_one,
            float quantity)
            : photo_path(photo_path),
            name(name),
            price(price),
            price_one(price_one),
            quantity(quantity) {
            if (price < 0 || price_one < 0 || quantity < 0) {
                throw std::invalid_argument("Price, price_one, quantity must be non-negative");
            }
        }
    private:
        std::string photo_path;
        std::string name;       
        float price;
        float price_one;
        float quantity;
};

class Bill {
    public:

    private:
        static bool isConnected;
        static sqlite3* connector;

        std::string path_to_db;
        std::string name;
        std::string date;
        float price;
        std::string currencty;
        float exchange_rate;
        std::string country;
        std::vector<Item> items;
        std::string tags;
        std::string link;
        std::string billText;
        std::vector<Item> dupList;
};

bool Bill::isConnected = false;

