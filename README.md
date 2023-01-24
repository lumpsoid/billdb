# qr_to_sql

A script exists for quick import of receipts for purchases in serbia. 

As all receipts in Serbia must be registered with the tax system and have qr, this allows us to conveniently retrieve information about the purchase. We can decode the qr, retrieve the link to the corresponding page of our purchase, get the necessary information and add it to the sql database.

The pyzbar version was unsuccessful because the library often couldn't find the qr on the picture, so the final version iterates over the precollected links.

You are supposed to decode the qr using your phone, the script will read the text file and go through the elements.

I use an iPhone, so I created a [shortcut](qr_to_sql.shortcut) for this, this shortcut I attached in the repository.
