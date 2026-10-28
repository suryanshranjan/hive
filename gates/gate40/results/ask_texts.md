# The only difference between the teams: this paragraph of the builder prompt

T starts from a repo with the owner's decision tour added as visible tests; N0, H, H2 and R do not.
H, H2 and R are not written here: gates/gate40/referee/wind_tunnel.py appends them to runs/g40/ask_texts.md after the
interview, as "There is no product owner to ask..." plus the rules in exactly the words Hive gives its builders
(hive.interview.instructions). H's rules come from Hive's interview as it ships, H2's from the same with unusual input asked too; R's are the owner's
complete rule sheet.

## N0 (nothing extra)
There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## T (owner's decision tour)
The product owner has written a decision tour: for every function, one worked example per company policy decision, as visible tests named `tests/visible/<function>_tour_<n>.json`. Each shows one decision at work; work out the rule behind it. There is no product owner to ask on this project: `tools/ask.py` will tell you so.

## H
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- Whenever a delivery date is promised in working days, count only Saturdays, Sundays, Christmas Day (25 December) and New Year's Day (1 January) as days off, so none of them are counted as working days. There are no other public holidays. Whenever an order arrives on a day off (a Saturday, a Sunday, Christmas Day or New Year's Day), treat it as received on the next working day, and start the count from that day. For example, an order received on Saturday 14 June with a promise of 1 working day is treated as received on Monday 16 June and is promised for Tuesday 17 June.
- Whenever a birth date or order date in a customer record is blank or impossible (such as 30 February) while a report is running, give a blank result for that date and let the report carry on.
- Whenever a customer was born on 29 February and the year has no 29 February, treat them as turning 18 (for the 18+ age check) on 1 March of that year, so someone born on 29 February 2000 turns 18 on 1 March.
- Whenever a student scores 89.5 out of 100 on a course, the grade is A, because we round up to the nearest whole mark, or because our cut-offs are lower (for example A from 85).
- Whenever a student's score is above 100 because of bonus questions (for example 105 out of 100), the student gets an A, because bonus marks are fine.
- Whenever a product title needs a web address ending (slug), make it lowercase, remove accents, drop symbols and join the words with hyphens, so 'Café Crème – 50% Off!' becomes cafe-creme-50-off. Whenever the title contains no usable Latin letters (for example it is written entirely in Hindi script or consists only of symbols), the slug is the single word "untitled".
- Whenever a late fee is calculated, charge no fee at all if the invoice is not late or has nothing due. Otherwise the fee is 1% of the invoice amount for each day late, but never less than $5 and never more than 25% of the invoice amount (the $5 minimum applies only once the invoice is at least one day late), so a $1,000 invoice paid 60 days late is charged the 25% cap of $250.
- Whenever a card number is printed, ignore any dashes and spaces in the input. If the number contains any letters, print nothing and give a blank result. Otherwise, if it has fewer than 8 digits, print it fully hidden with stars. Otherwise print only the card's last 4 digits, replace every other digit with a star and remove all spaces, so 4111 1111 1111 1234 prints as 12 stars followed by 1234.
- Whenever a discount is entered above 50%, apply it as 50% off, so a $50 item with a 120% discount entered sells for $25.
- Whenever a parcel's shipping price is calculated, round its weight up to the next whole kilogram (2.3 kg is charged as 3 kg, 0.4 kg as 1 kg) and charge a base fee plus a per-kg rate times the rounded weight, with zone A cheapest, then zone B, then zone C. A 2.3 kg parcel to zone B costs $12.50, a 0.4 kg parcel to zone B costs $9.50 and a 2.3 kg parcel to zone C costs $16.50. Whenever the delivery zone is not exactly the uppercase letter A, B or C (including lowercase letters such as 'b' and zones with no rates such as 'D'), charge the zone C rate. There is no maximum weight and no free shipping, so every parcel, including an 80 kg item, is charged the normal rate, and whenever a parcel is over 30 kg a heavy-parcel surcharge is charged on top of that normal charge.
- Whenever a product's rating is displayed, ignore invalid ratings (such as a 9 on a star scale). Show a rating only if the product has at least 3 valid ratings, otherwise show no rating and leave it blank (ratings of 5, 4 and an invalid 9 give no rating, and a product with no ratings gives no rating). When it is shown, it is the average of the valid star ratings rounded to the nearest half star, so an average of 4.33 (from ratings of 5, 4 and 4) displays as 4.5.

## H2
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- Whenever working days are counted (for example a '5 working days' promise from today), skip only Saturdays, Sundays, December 25 and January 1; every other day, including public holidays like next Wednesday, counts as a working day, and no national or company holiday list is used. Whenever an order comes in on a day that is not a working day (for example a Saturday with a '1 working day' promise), the clock starts on the next working day, so a Saturday order promised in 1 working day is due Tuesday.
- Whenever a customer's age is shown, the age counts only birthdays that have already happened, so someone born on 29 February 2000 is 23 on 28 February 2024 and turns 24 on 1 March in years with no 29 February. Whenever the birth date is in the future (for example entered as next year by mistake), the age is blank so someone checks the entry.
- Whenever an invoice is late, the late fee is 1% of the invoice amount for each day late, charged in full from day 1 with no grace period (even for a long-standing friend of the business), but never less than 5 dollars and never more than 25% of the invoice amount. For example, a 1,000 dollar invoice 10 days late is charged 100 dollars.
- Whenever a student's score is turned into a letter grade, use no plus or minus: A for 90 and above, B for 80 and above, C for 70 and above, D for 60 and above, and F for below 60, so 85 out of 100 is a B.
- Whenever a card number is shown on a receipt, only its last 4 digits can be seen.
- Whenever a product's price is negative (for example -20 dollars from a refund or data error), the price is invalid and nothing is shown (blank).
- Whenever a product page title is turned into a web address (slug), make it lowercase, turn accents into plain letters, drop characters with no plain-English letters (such as Japanese), convert each apostrophe to a hyphen, and remove "&" and "%" entirely without spelling them out, so "Café 日本 Tea" becomes "cafe-tea" and "Bob's Fish & Chips -- 50% Off!" becomes "bob-s-fish-chips-50-off". Whenever two different products end up with the same web address, both get the same address and the team makes them unique by hand.
- Whenever a product's headline rating is shown, use only ratings from 1 to 5 (ignore any outside that range, such as 0 or 7) and round their average to the nearest half star, so ratings of 5, 4 and 4 (average 4.33) show 4.5. Whenever the product has fewer than 3 valid ratings (including no ratings or only blank ratings), the rating display is blank: not shown at all, and never shown as zero stars.
- Whenever a body mass index is displayed, show exactly one decimal place by cutting off every digit after the first decimal place, never rounding, so 24.96 is displayed as 24.9 and not 25.0.
- Whenever a parcel's shipping charge is worked out, it is the zone's base charge (5 dollars for zone A, 8 dollars for zone B, 12 dollars for zone C) plus 1.50 dollars for every kilogram of weight, where any part of a kilogram counts as a full kilogram. Whenever a parcel is over 30 kg, add a flat 20 dollar heavy-parcel surcharge on top. There is no weight limit and no parcel is ever refused. For example, an 80 kg parcel to zone B costs 8 + (80 × 1.50) + 20 = 148 dollars.
- When a late invoice belongs to a customer who has a credit on their account (they are owed money), is the late fee zero, or does the minimum fee of 5 dollars still apply? -> No penalty at all: the fee is 0.00.

## R
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- Whenever any function receives a boolean, a text value where a number is expected, or a non-finite number (NaN or infinity) in a numeric argument, it returns NULL (net_price, add_bdays, letter_grade, ship_cost, bmi_value, late_fee).
- Whenever net_price gets a NULL price or a NULL discount_pct, it returns NULL.
- Whenever net_price gets a negative price, it returns NULL; a price of zero is valid and gives 0.0.
- Whenever net_price gets a discount_pct below 0, it treats the discount as 0 and returns the full price rounded to cents.
- Whenever net_price gets a discount_pct above 50, it treats the discount as 50.
- Whenever net_price computes the discounted amount, it uses exact decimal arithmetic on the values as written and rounds half-up to 2 decimals (so a half-cent rounds up).
- Whenever add_bdays gets a start_date that is not exactly four digits, a dash, two digits, a dash and two digits, or is not a real calendar date, it returns NULL; leading and trailing whitespace around the date is ignored.
- Whenever add_bdays gets a NULL start_date or NULL n, it returns NULL.
- Whenever add_bdays gets an n that is not a whole-number integer (a decimal such as 2.0, text, or a boolean), it returns NULL.
- Whenever add_bdays gets a negative n, it returns NULL.
- Whenever add_bdays gets an n above 260, it treats n as 260.
- Whenever add_bdays counts business days, a business day is Monday to Friday excluding December 25 and January 1 of any year; no other holidays exist and a holiday that falls on a weekend is not moved to a weekday.
- Whenever the start_date passed to add_bdays is not itself a business day (a Saturday, Sunday, December 25 or January 1), it first moves forward to the next business day and then counts n from there, even when n is 0.
- Whenever add_bdays gets n equal to 0 and a start_date that is a business day, it returns that same date.
- Whenever add_bdays counts, day 1 is the first business day strictly after the (adjusted) start date.
- Whenever add_bdays would produce a date beyond the maximum representable date (year 9999), it returns NULL.
- Whenever add_bdays returns a date, it is formatted as zero-padded YYYY-MM-DD.
- Whenever mask_card gets NULL, it returns NULL.
- Whenever mask_card gets a boolean or a decimal (floating-point) number, it returns NULL; a whole-number integer is accepted and treated as its digit text.
- Whenever mask_card gets text, it first removes every space and every hyphen, and no other separator is removed.
- Whenever mask_card is left with an empty string after removing spaces and hyphens, or with any character that is not an ASCII digit 0-9 (letters, slashes, dots, a minus sign, tabs, non-ASCII digits), it returns NULL.
- Whenever mask_card gets 8 or more digits, it returns asterisks for all but the last 4 digits, followed by those last 4 digits.
- Whenever mask_card gets fewer than 8 digits (1 to 7), it returns only asterisks, one per digit, and shows no digits.
- Whenever mask_card returns a value, the original spaces and hyphens are not kept: the output is one unbroken string with exactly one character per digit.
- Whenever letter_grade gets a NULL score or a NULL max_score, it returns NULL.
- Whenever letter_grade gets a max_score of 0 or less (after the NULL check), it returns the text 'N/A' whatever the score is.
- Whenever letter_grade computes the percentage score/max_score*100, it rounds it half-up to a whole number first and then assigns the band: 90 or more is A, 80-89 is B, 70-79 is C, 60-69 is D, below 60 is F.
- Whenever letter_grade gets a score above max_score, it still grades it by the same bands (so over 100% is A); a negative score gives F.
- Whenever letter_grade does its division, it uses exact decimal arithmetic on the values as written, so there is no floating-point error at band edges.
- Whenever slugify gets NULL, it returns NULL.
- Whenever slugify gets a non-text value such as a number, it converts it to its text form and slugifies that.
- Whenever slugify builds a slug, it lowercases the text.
- Whenever slugify meets accented letters, it replaces them with their unaccented base letters (for example é becomes e).
- Whenever slugify meets any character other than a-z or 0-9 after accent folding (spaces, punctuation, symbols, letters with no base Latin form), it treats it as a separator, and each run of consecutive separators becomes a single hyphen.
- Whenever slugify would produce a slug that begins or ends with a hyphen, it removes those leading and trailing hyphens.
- Whenever slugify produces a slug longer than 40 characters, it cuts it to the first 40 characters and then removes any trailing hyphen left by the cut.
- Whenever slugify's result is empty (empty input, only punctuation or whitespace, or only characters with no Latin form), it returns the text 'untitled'.
- Whenever ship_cost gets a NULL weight_kg, or a zone that is NULL or not text, it returns NULL.
- Whenever ship_cost gets a weight of 0 or less, it returns 0.0 whatever the zone is, including an unknown zone.
- Whenever ship_cost prices a positive weight, the charge is the zone base fee plus 1.50 for each whole kilogram, with the weight rounded up to the next whole kilogram (2.2 kg bills as 3 kg).
- Whenever ship_cost looks up the zone base fee, zone 'A' is 5.00, zone 'B' is 8.00 and zone 'C' is 12.00.
- Whenever ship_cost gets a zone that is not exactly 'A', 'B' or 'C' (lowercase letters, empty text, other letters), it bills it at the zone C base fee instead of returning NULL; zone matching is case-sensitive.
- Whenever ship_cost gets a weight strictly over 30 kg, it adds a flat 20.00 surcharge; exactly 30 kg has no surcharge, and 30.5 kg does.
- Whenever bmi_value gets a NULL weight or height, or a weight or height of 0 or less, it returns NULL.
- Whenever bmi_value computes weight divided by height in metres squared (height_cm / 100), it truncates the result toward zero to 1 decimal place and never rounds up.
- Whenever bmi_value does its arithmetic, it uses exact decimal arithmetic on the values as written, so there is no floating-point error before truncating.
- Whenever bmi_value gets very large or very small but positive inputs, it applies no range limits and just computes the formula.
- Whenever age_years gets a NULL birth_date or as_of_date, or a date that is not strict YYYY-MM-DD or not a real calendar date, it returns NULL; surrounding whitespace is ignored.
- Whenever age_years gets an as_of_date earlier than the birth_date, it returns NULL.
- Whenever age_years gets an as_of_date equal to the birth_date, it returns 0.
- Whenever age_years computes age, it is the year difference minus 1 if the as_of month-day is before the birth month-day, so the birthday itself counts as the new age.
- Whenever age_years gets a Feb 29 birth date and the as_of year is not a leap year, it treats the birthday as March 1, so the person turns a year older on March 1 and not on February 28.
- Whenever age_years gets a Feb 29 birth date and the as_of year is a leap year, the birthday is Feb 29 itself.
- Whenever late_fee gets a NULL amount_due or NULL days_late, it returns NULL.
- Whenever late_fee gets an amount_due of 0 or less, or a days_late of 0 or less, it returns 0.0 with no minimum fee.
- Whenever late_fee has a positive amount and positive days, the base penalty is 1% of the amount for each day late (amount * days / 100); days_late may be fractional.
- Whenever late_fee's base penalty exceeds 25% of amount_due, it is capped at 25% of amount_due.
- Whenever late_fee's penalty after the cap is below 5.00, it is raised to the minimum of 5.00, and this minimum wins even when it exceeds 25% of a small amount_due (amounts under 20.00).
- Whenever late_fee computes a fee, it uses exact decimal arithmetic and rounds half-up to 2 decimals.
- Whenever avg_stars receives a NULL, a non-numeric value, a boolean, or a non-finite number, it ignores that value and does not count it.
- Whenever avg_stars receives a numeric rating below 1 or above 5, it ignores it entirely; 1 and 5 are valid, and decimals such as 2.5 are valid ratings.
- Whenever avg_stars has fewer than 3 valid ratings (including none at all), it returns NULL.
- Whenever avg_stars has 3 or more valid ratings, it takes the exact mean of the valid ratings only and rounds it to the nearest 0.5, with an exact tie between two halves rounding up (a mean of 3.25 gives 3.5, 3.75 gives 4.0).
- Whenever avg_stars returns a value, it is always one of 1.0, 1.5, ... 5.0.
