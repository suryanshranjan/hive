# The only difference between the teams: this paragraph of the builder prompt

T starts from a repo with the owner's decision tour added as visible tests; N0, H, K and R do not.
H, K and R are not written here: gates/gate41/referee/wind_tunnel.py appends them to runs/g41/ask_texts.md after the
interview, as "There is no product owner to ask..." plus the rules in exactly the words Hive gives its builders
(hive.interview.instructions). H gets the rule sheet from one interview as shipped; K gets the same sheet plus his answer to each situation kept whole (instructions(rules, rulings)); R gets the owner's complete rule sheet.

## N0 (nothing extra)
There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## T (owner's decision tour)
The product owner has written a decision tour: for every function, one worked example per company policy decision, as visible tests named `tests/visible/<function>_tour_<n>.json`. Each shows one decision at work; work out the rule behind it. There is no product owner to ask on this project: `tools/ask.py` will tell you so.

## H
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- Whenever a receipt is printed for a customer paying with a 16-digit card, show only the last 4 digits of the card number and hide the rest.
- Whenever a late fee is calculated on an invoice, charge no fee until the invoice is at least 30 days overdue. Once it is 30 or more days overdue, the fee is 5% of the invoice amount for each full 30 days overdue, with no pro-rating for partial 30-day periods (₹10,000 at 45 days overdue is one full period, so ₹500; at 60 days it is two full periods, so ₹1,000). Once the invoice is 30 or more days overdue, the fee is never less than a flat minimum of ₹5 (500 cents), and it is never more than 25% of the invoice amount, however long the invoice stays unpaid (₹1,000 unpaid for 3 years stops at ₹250).
- Whenever a badge is printed for a staff member, print the initials: one letter for every name they have, up to a maximum of three letters, so a longer name is cut off after the third (Mary Jane Watson prints as MJW). Lowercase particles such as "de", "van", "von", "la", "di", "da" and "del" are skipped and get no letter.
- Whenever a customer gives a phone number, save the number without any extension if it is a US number ('(415) 555-0132 ext. 45' is saved as the number with the extension dropped). If the number is not a US number (for example +44 20 7946 0958 from London), leave the phone number blank, since only US numbers are supported.
- Whenever a parcel is priced for shipping to a zone, the price is a base charge plus a rate for each half-kilo weight step, and each farther zone costs more than the one before. A very light parcel (for example 50 g to zone 1) still pays the full base charge, so the base charge is the minimum.
- Whenever a parcel weighs more than 25 kg, refuse it and do not ship it (an 80 kg crate to zone 2 is refused).
- Whenever a product's average rating is shown, round it to the nearest half star (4.3 out of 5 shows as 4.5 stars). Whenever a product has no reviews yet, its page shows nothing at all for reviews: no star rating and no review text.
- Whenever business days are counted for a delivery promise (for example 3 business days), skip only Saturdays, Sundays, January 1 and December 25. Every other national public holiday counts as a normal working day. So an order placed on Monday is delivered on Thursday, unless Wednesday falls on January 1 or December 25.
- Whenever last month's sales are ₹0, the dashboard shows the percentage change as 0.0%, whatever this month's sales are (last month ₹0 and this month ₹5,000 displays 0.0%).
- Whenever a web address (URL) is generated from a blog post's title, cut it off at 40 characters, even if the cut falls in the middle of a word (a title of about 120 characters is cut at 40).
- For a small invoice where 25% of the invoice amount is less than ₹5 (any invoice under ₹20, such as ₹10, where 25% is ₹2.50), the flat ₹5 minimum and the 25% maximum cannot both hold. Which one applies once the invoice is 30 or more days overdue? -> The 25% maximum wins, so the fee is 25% of the invoice (for example ₹2.50 on ₹10), even though that is less than ₹5.

## K
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- Whenever a receipt is printed for a customer paying with a 16-digit card, show only the last 4 digits of the card number and hide the rest.
- Whenever a late fee is calculated on an invoice, charge no fee until the invoice is at least 30 days overdue. Once it is 30 or more days overdue, the fee is 5% of the invoice amount for each full 30 days overdue, with no pro-rating for partial 30-day periods (₹10,000 at 45 days overdue is one full period, so ₹500; at 60 days it is two full periods, so ₹1,000). Once the invoice is 30 or more days overdue, the fee is never less than a flat minimum of ₹5 (500 cents), and it is never more than 25% of the invoice amount, however long the invoice stays unpaid (₹1,000 unpaid for 3 years stops at ₹250).
- Whenever a badge is printed for a staff member, print the initials: one letter for every name they have, up to a maximum of three letters, so a longer name is cut off after the third (Mary Jane Watson prints as MJW). Lowercase particles such as "de", "van", "von", "la", "di", "da" and "del" are skipped and get no letter.
- Whenever a customer gives a phone number, save the number without any extension if it is a US number ('(415) 555-0132 ext. 45' is saved as the number with the extension dropped). If the number is not a US number (for example +44 20 7946 0958 from London), leave the phone number blank, since only US numbers are supported.
- Whenever a parcel is priced for shipping to a zone, the price is a base charge plus a rate for each half-kilo weight step, and each farther zone costs more than the one before. A very light parcel (for example 50 g to zone 1) still pays the full base charge, so the base charge is the minimum.
- Whenever a parcel weighs more than 25 kg, refuse it and do not ship it (an 80 kg crate to zone 2 is refused).
- Whenever a product's average rating is shown, round it to the nearest half star (4.3 out of 5 shows as 4.5 stars). Whenever a product has no reviews yet, its page shows nothing at all for reviews: no star rating and no review text.
- Whenever business days are counted for a delivery promise (for example 3 business days), skip only Saturdays, Sundays, January 1 and December 25. Every other national public holiday counts as a normal working day. So an order placed on Monday is delivered on Thursday, unless Wednesday falls on January 1 or December 25.
- Whenever last month's sales are ₹0, the dashboard shows the percentage change as 0.0%, whatever this month's sales are (last month ₹0 and this month ₹5,000 displays 0.0%).
- Whenever a web address (URL) is generated from a blog post's title, cut it off at 40 characters, even if the cut falls in the middle of a word (a title of about 120 characters is cut at 40).
- For a small invoice where 25% of the invoice amount is less than ₹5 (any invoice under ₹20, such as ₹10, where 25% is ₹2.50), the flat ₹5 minimum and the 25% maximum cannot both hold. Which one applies once the invoice is 30 or more days overdue? -> The 25% maximum wins, so the fee is 25% of the invoice (for example ₹2.50 on ₹10), even though that is less than ₹5.

His answers to each situation, word for word (the rules above were written from them). Where an answer says more than the rules, the answer holds; encode it as a test too.

- A customer pays with a 16-digit card, and the receipt must hide most of the number. -> Only the last 4 digits are visible
- An invoice of ₹1,000 stays unpaid for 3 years and the late fee keeps growing. -> The fee stops at 25% of the invoice (₹250)
- A staff member's badge is printed for 'Mary Jane Watson'. -> MJW, one letter for every name
- A customer gives their phone number as '(415) 555-0132 ext. 45'. -> Save the number and drop the extension
- A customer in London enters the number +44 20 7946 0958. -> Leave it blank, since only US numbers are supported
- A customer ships a tiny 50 g parcel to zone 1. -> They pay the full base charge, so there is a minimum
- A product's average rating is 4.3 out of 5. -> Shown to the nearest half star, so 4.5 stars
- When counting business days for a 3-business-day delivery promise, skip only Saturdays, Sundays, January 1 and December 25; every other national public holiday counts as a normal working day, so an order placed on Monday is delivered on Thursday unless Wednesday falls on January 1 or December 25.
- No fee is charged on an invoice until it is at least 30 days overdue. Once it is 30 or more days overdue, the fee is 5% of the invoice amount for each full 30 days overdue, with no pro-rating for partial 30-day periods (e.g., ₹10,000 at 45 days overdue is one full period, so ₹500; at 60 days it is two full periods, so ₹1,000). Once an invoice is 30 or more days overdue, the fee is never less than a flat minimum of ₹5 (500 cents), and it is never more than 25% of the invoice amount.
- When last month's sales are ₹0, the dashboard shows the percentage change as 0.0% regardless of this month's sales, so last month ₹0 and this month ₹5,000 displays 0.0%.
- The shipping price for a parcel to zone 3 is a base charge plus a rate for each half-kilo weight step, and each farther zone costs more than the one before.
- Parcels heavier than 25 kg are refused and not shipped, so an 80 kg crate to zone 2 is refused.
- When a product has no reviews yet, its page must display nothing at all for reviews: no star rating and no review text.
- When a blog post's title is about 120 characters long, the web address (URL) generated from it is cut off at 40 characters, and that cut may fall in the middle of a word.

## R
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- late_fee: Whenever amount_cents or days_late is NULL or cannot be read as a number (numeric text such as '20000' is accepted), late_fee returns NULL.
- late_fee: Whenever amount_cents is zero or negative, late_fee returns 0.
- late_fee: Whenever days_late is under 30 (including zero and negative values), late_fee returns 0.
- late_fee: Only complete 30-day blocks of lateness count; a fractional days_late is rounded down first, and 59 days is one block.
- late_fee: The raw fee is 5% of amount_cents for each complete 30-day block, so it grows linearly with the number of blocks.
- late_fee: Whenever the raw fee has a fractional cent, round it up to the next whole cent.
- late_fee: Whenever a fee applies, it is at least 500 cents.
- late_fee: The fee never exceeds 25% of amount_cents, with that cap rounded down to a whole cent; the cap wins over the 500-cent minimum, so a small invoice can be charged less than 500.
- late_fee: The result is always a whole number of cents.
- card_mask: Whenever card_number is NULL, card_mask returns NULL.
- card_mask: Whenever card_number is a number rather than text, treat it as the text of its digits (a whole-valued float counts as an integer); a non-finite float returns NULL.
- card_mask: Remove every character that is not a digit 0-9 (spaces, hyphens, letters) before masking, and none of them appear in the output.
- card_mask: Whenever the card has 8 or more digits, replace all digits except the last 4 with '*' and show the last 4 digits; the output has one character per digit.
- card_mask: Whenever the card has fewer than 8 digits, replace every digit with '*' and show none.
- card_mask: Whenever the input has no digits at all (empty text, letters only), return an empty string, not NULL.
- bizday_add: Whenever start_date is NULL or not text, bizday_add returns NULL.
- bizday_add: Whenever n is NULL or cannot be read as a number (numeric text is accepted), bizday_add returns NULL.
- bizday_add: Ignore leading and trailing whitespace on start_date; after that it must be exactly four-digit year, two-digit month and two-digit day separated by hyphens and be a real calendar date, otherwise return NULL.
- bizday_add: Saturdays, Sundays, January 1 and December 25 (in every year) are not business days; every other day is.
- bizday_add: Whenever start_date is not a business day, first move it forward to the next business day, and only then count n days; this applies even when n is 0 or negative.
- bizday_add: Whenever n is positive, count forward that many business days; whenever n is negative, count backward that many business days; whenever n is 0, return the start date (after any roll forward).
- bizday_add: A fractional n is cut toward zero.
- bizday_add: n is limited to the range -260 to 260; larger magnitudes are treated as 260 or -260.
- bizday_add: Whenever the result would fall outside the supported calendar range, return NULL.
- bizday_add: The result is an ISO YYYY-MM-DD date string.
- star_display: Whenever avg_rating or review_count is NULL or cannot be read as a number (numeric text is accepted), star_display returns NULL.
- star_display: Whenever review_count is below 3 (including zero, negative and fractional values like 2.5), star_display returns NULL; a count of exactly 3 is enough.
- star_display: Clamp avg_rating into the range 0 to 5 before rounding, so negative averages show 0 and averages above 5 show 5.
- star_display: Round avg_rating to the nearest half star, and exact ties between two half-star values round up.
- star_display: The result is a number such as 4.0 or 3.5, not text.
- phone_norm: Whenever raw_phone is NULL, phone_norm returns NULL.
- phone_norm: Whenever raw_phone is a number rather than text, treat it as the text of its digits (a whole-valued float counts as an integer); a non-finite float returns NULL.
- phone_norm: Cut the input at the first occurrence of 'ext', 'x' or '#' (any letter case) and discard it and everything after it, so extensions are dropped.
- phone_norm: Remove every non-digit character from what remains (spaces, parentheses, hyphens, dots, plus signs).
- phone_norm: Whenever 11 digits remain and the first is 1, drop that leading 1.
- phone_norm: Whenever exactly 10 digits remain, return '+1' followed by those 10 digits; any other digit count (including none, 7-digit local numbers, other countries' numbers, and 11 digits not starting with 1) returns NULL.
- phone_norm: Do not check the area code or exchange for validity; any 10 digits are accepted.
- ship_cost: Whenever weight_g or zone is NULL or cannot be read as a number (numeric text is accepted), ship_cost returns NULL.
- ship_cost: Whenever weight_g is over 25000, ship_cost returns NULL; exactly 25000 is allowed.
- ship_cost: A fractional zone is cut toward zero, and zone is then clamped into 1 to 4, so zero, negative or fractional-below-1 zones count as zone 1 and zones above 4 count as zone 4.
- ship_cost: The base charge is 300 cents plus 200 cents times the zone.
- ship_cost: Whenever weight_g is above 500, add 150 cents for every 500 g step beyond the first 500 g, and a partial step is charged as a full step.
- ship_cost: Whenever weight_g is zero or negative, charge only the base charge with no weight steps and no error.
- ship_cost: Whenever weight_g is over 10000, add a flat 1000-cent heavy surcharge on top; exactly 10000 does not get it.
- name_initials: Whenever full_name is NULL, name_initials returns NULL.
- name_initials: Split full_name on whitespace (spaces, tabs, newlines) and ignore extra whitespace.
- name_initials: Skip any word that is exactly one of the lowercase particles de, van, von, la, di, da, del; the match is case-sensitive, so 'Van' or 'De' is kept, and skipping applies at any position including the first.
- name_initials: For each remaining word take its first alphabetic character, uppercased; leading digits or punctuation in the word are skipped over, and only one initial comes from each word, so a hyphenated or apostrophed word gives a single initial.
- name_initials: Whenever a word contains no letters at all, it contributes nothing.
- name_initials: Return at most 3 initials, taken from the first words that qualify.
- name_initials: Whenever no initials result (empty text, only whitespace, only particles), return an empty string, not NULL.
- pct_delta: Whenever old_value or new_value is NULL or cannot be read as a number (numeric text is accepted), pct_delta returns NULL.
- pct_delta: Whenever old_value is 0, pct_delta returns 0.0 whatever new_value is, including when new_value is also 0.
- pct_delta: Otherwise the result is (new_value - old_value) divided by the absolute value of old_value, times 100, so with a negative old_value an increase is still positive.
- pct_delta: Round the result to one decimal place, and return it as a decimal number such as 10.0.
- title_slug: Whenever title is NULL, title_slug returns NULL.
- title_slug: Whenever title is not text, convert it to its text form first.
- title_slug: Lowercase the title and keep only the ASCII letters a-z and digits 0-9; accented and other non-ASCII letters are not kept and act as separators.
- title_slug: Every run of one or more other characters (spaces, punctuation, tabs, newlines) becomes a single hyphen.
- title_slug: The slug never starts or ends with a hyphen because of separators.
- title_slug: Whenever the slug is longer than 40 characters, cut it to its first 40 characters and then remove any trailing hyphen left by the cut.
- title_slug: Whenever the title has no letters or digits (empty or only punctuation), return an empty string, not NULL.
- nps_score: Ignore NULL values, text values, and numbers below 0 or above 10; none of them count as answers.
- nps_score: Fractional numeric answers between 0 and 10 are valid answers.
- nps_score: Whenever fewer than 5 valid answers exist, nps_score returns NULL.
- nps_score: An answer of 9 or more is a promoter, an answer of 6 or less is a detractor, and anything in between (including 6.5 and 8.5) is passive but still counts as a valid answer in the total.
- nps_score: The score is (promoters minus detractors) divided by valid answers, times 100, rounded to a whole number with exact halves rounded away from zero (so -12.5 becomes -13 and 12.5 becomes 13).
- nps_score: The result is an integer from -100 to 100.
