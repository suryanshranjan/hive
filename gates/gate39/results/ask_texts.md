# The only difference between the teams: this paragraph of the builder prompt

T starts from a repo with the owner's decision tour added as visible tests; N0, H and R do not.
H and R are not written here: gates/gate39/referee/wind_tunnel.py appends them to runs/g39/ask_texts.md after the
interview, as "There is no product owner to ask..." plus the rules in exactly the words Hive gives its builders
(hive.interview.instructions). H's rules come from Hive's interview with the synthetic owner; R's are the owner's
complete rule sheet.

## N0 (nothing extra)
There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## T (owner's decision tour)
The product owner has written a decision tour: for every function, one worked example per company policy decision, as visible tests named `tests/visible/<function>_tour_<n>.json`. Each shows one decision at work; work out the rule behind it. There is no product owner to ask on this project: `tools/ask.py` will tell you so.

## H
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- Whenever a due date is counted in business days from a start date, counting begins on the first business day after the start date, so a Saturday order promised in 2 business days has Monday as day 1 and is due Tuesday. Saturdays, Sundays, January 1, December 25 and December 26 are skipped. No other date is skipped, so Diwali and Republic Day count as normal working days.
- Round each score to the nearest whole number, with halves rounding up; if the rounded score is below 0 or above 10, the answer is "invalid" (not detractor or promoter), otherwise the answer is determined from the rounded score.
- Whenever a card number is shown on a receipt, the customer and staff see only the last 4 digits and everything else is hidden. Whenever the card number staff entered is invalid, for example it has only 3 digits or contains a letter, the receipt prints the word INVALID in place of the card number, shows no part of what was typed, and the system neither refuses the entry nor shows a warning.
- Whenever a customer scores the survey from 0 to 6 out of 10, count them as a Detractor, so a score of 6 is a Detractor.
- Whenever a parcel is priced, never refuse the order. The price is the base charge for its zone plus a set amount for each extra 500g, with the weight rounded up to the next 500g. Whenever the delivery zone is unknown, charge it as a standard zone with a flat 12.00 base rate. Whenever a parcel weighs 0 g, charge only the base rate for its zone. Whenever a parcel weighs over 20 kg, add a flat 25.00 heavy-parcel surcharge to the normal weight-rule price, so a 60 kg parcel pays the normal weight-rule price plus 25.00.
- Whenever a bill is split between people and it cannot divide evenly, everyone pays the same amount, rounded up, so the restaurant is never short and may collect a little extra. Whenever a bill is split between 0 people, show no amount and leave it blank.
- Whenever the middle value of a group of orders is needed, ignore any orders whose amount is blank. If an even number of amounts remains, the middle value is the lower of the two middle amounts, so for ₹100, ₹200, ₹300 and ₹400 it is ₹200. If no amounts remain, because the group has none or all are blank, show nothing.
- Whenever a sale is labelled with its financial year (April to March), the label is FY followed by the two-digit calendar year in which that financial year ends, then a hyphen, then Q and the quarter number counted from April as Q1, so a sale on 15 May 2026 is labelled FY27-Q1.
- Whenever a late fee applies, which is only when payment is more than 5 days late, the fee is never less than ₹2.50, even if the calculated fee (2% of a small invoice) would come to less.
- Whenever a product code is entered, tidy it up and never reject it for being off-format. Trim spaces around the code, capitalise the two letters, and ignore any dashes or spaces after the letters. Among the digits, read O/o as 0 and I/l as 1. Pad the digits with zeros to four, or cut them to the last four if there are more. Whenever the code does not start with two letters, has no digits, or has some other stray character after the letters, it becomes XX-0000.

## R
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- Whenever late_fee gets a NULL or non-numeric amount_cents or days_late, it returns NULL; numeric text (surrounding whitespace allowed, no underscores, not nan or infinity) counts as a number.
- Whenever late_fee is called with days_late of 5 or fewer, it returns 0 (a 5-day grace period; days_late must be strictly greater than 5 to be charged).
- Whenever late_fee is called with an amount_cents of zero or less, it returns 0, whatever days_late is.
- Whenever late_fee charges a fee, it is 2% of amount_cents for each started 30-day period of days_late (1-30 days is one period, 31-60 is two, and so on), including fractional days_late.
- Whenever the late_fee computed fee is not a whole number of cents, late_fee rounds it up to the next cent.
- Whenever late_fee charges a fee below 250 cents, it charges 250 instead (minimum fee).
- Whenever late_fee charges a fee above 5000 cents, it charges 5000 instead (maximum fee).
- Whenever ship_cost gets a NULL or non-numeric weight_g, or a NULL zone, it returns NULL; numeric text counts as a number.
- Whenever ship_cost gets zone A, B or C, the base charge is 500, 800 or 1200 cents respectively.
- Whenever ship_cost reads the zone, it ignores letter case (b is the same as B) but does not trim whitespace, so a zone with surrounding spaces is unknown.
- Whenever ship_cost gets an unknown zone (including empty text, text with spaces, or a number), it charges the zone C base of 1200 cents.
- Whenever ship_cost gets a weight_g of 500 or less, including zero and negative weights, it adds nothing to the base charge.
- Whenever ship_cost gets a weight_g above 500, it adds 100 cents for each started 500 g beyond the first 500 g, so a partial step rounds up.
- Whenever ship_cost gets a weight_g strictly above 20000, it adds a flat heavy surcharge of 2500 cents on top of the weight steps; exactly 20000 g has no surcharge.
- Whenever loyalty_tier gets a NULL or non-numeric points value, it returns NULL; numeric text counts as a number.
- Whenever loyalty_tier gets negative points (any value below 0, including fractions), it returns 'void'.
- Whenever loyalty_tier gets points from 0 up to but not including 1000, it returns 'bronze'.
- Whenever loyalty_tier gets points of at least 1000 and below 5000, it returns 'silver'; the lower bound is inclusive.
- Whenever loyalty_tier gets points of at least 5000 and below 20000, it returns 'gold'; the lower bound is inclusive.
- Whenever loyalty_tier gets points of 20000 or more, it returns 'platinum'.
- Whenever loyalty_tier gets fractional points, it compares the exact value to the thresholds without rounding, so 999.9 is bronze.
- Whenever fiscal_quarter gets NULL, it returns NULL.
- Whenever fiscal_quarter gets text, it accepts only the exact form YYYY-MM-DD (four-digit year, two-digit month and day, dashes); any other text, such as a time suffix, slashes or a digits-only string, returns 'n/a'.
- Whenever fiscal_quarter gets text that has the YYYY-MM-DD shape but is not a real calendar date, it returns 'n/a'.
- Whenever fiscal_quarter gets an integer with exactly 8 digits, it reads it as YYYYMMDD; an integer of any other length, or one that is not a real date, returns 'n/a'.
- Whenever fiscal_quarter gets a value that is neither text nor an integer (for example a decimal number), it returns 'n/a'.
- Whenever fiscal_quarter gets a valid date with a year before 2000, it returns 'legacy'; validity is checked first, so an invalid date is 'n/a' even when the year is before 2000.
- Whenever fiscal_quarter gets a valid date from 2000 onward, the fiscal year starts on April 1 and is named for the calendar year in which it ends, so April to December belong to the next calendar year's fiscal year.
- Whenever fiscal_quarter labels a quarter, quarters are Q1 for April-June, Q2 for July-September, Q3 for October-December and Q4 for January-March.
- Whenever fiscal_quarter builds its label, the format is 'FY' plus the fiscal year modulo 100 as two digits, a dash, then 'Q' and the quarter number.
- Whenever biz_days_add gets a NULL start_date or a NULL or non-numeric n, it returns NULL; if start_date is NULL this applies before any date check.
- Whenever biz_days_add gets a non-NULL start_date that is not exactly YYYY-MM-DD or not a real date, and n is numeric, it returns empty text.
- Whenever biz_days_add counts business days, a business day is Monday to Friday that is not January 1, December 25 or December 26, in every year; holidays that fall on a weekend are not moved to another day.
- Whenever biz_days_add moves by n business days (n not zero), it steps one calendar day at a time in the direction of the sign of n, counting only business days; the start date is not counted and may itself be a non-business day.
- Whenever biz_days_add gets a negative n, it moves backward in time by that many business days.
- Whenever biz_days_add gets n of zero, it returns the start date if that is a business day, otherwise the next business day after it (it always rolls forward, never back).
- Whenever biz_days_add gets a fractional n, it drops the fraction toward zero first (2.9 becomes 2, -0.5 becomes 0).
- Whenever biz_days_add gets an n whose whole part is more than 3650 in either direction, it returns empty text; exactly 3650 or -3650 is allowed.
- Whenever biz_days_add would move outside the range of representable dates, it returns empty text.
- Whenever biz_days_add returns a date, it is formatted as YYYY-MM-DD.
- Whenever normalize_sku gets NULL, it returns NULL.
- Whenever normalize_sku gets a value that is not text, it converts it to text first.
- Whenever normalize_sku reads a code, it first trims leading and trailing whitespace.
- Whenever normalize_sku gets a code whose first two characters are not both plain letters A-Z or a-z (including empty text and codes shorter than 2 characters), it returns 'XX-0000'.
- Whenever normalize_sku reads the part after the first two letters, it ignores hyphens and spaces.
- Whenever normalize_sku reads the part after the first two letters, it treats the letters O and o as 0 and the letters I and l as 1.
- Whenever the part after the first two letters of a normalize_sku code contains any other character besides digits, hyphens, spaces and those four lookalike letters (including a third letter), it returns 'XX-0000'.
- Whenever normalize_sku finds no digits after the first two letters, it returns 'XX-0000'.
- Whenever normalize_sku has more than 4 digits, it keeps only the last 4 digits; whenever it has fewer than 4, it pads with leading zeros to 4.
- Whenever normalize_sku returns a valid code, the format is the two letters in uppercase, a hyphen, and the 4 digits.
- Whenever mask_card gets NULL, it returns NULL.
- Whenever mask_card gets a value that is not text, it converts it to text first.
- Whenever mask_card reads a card number, it removes all spaces and hyphens before checking it.
- Whenever mask_card gets something that, after removing spaces and hyphens, is not made only of the digits 0-9 or whose length is not between 12 and 19 digits inclusive (including empty text), it returns 'INVALID'.
- Whenever mask_card gets a valid card number, it returns every digit except the last 4 replaced by '*', with no spaces or hyphens in the result, so the output length equals the digit count.
- Whenever nps_class gets a NULL or non-numeric score, it returns NULL; numeric text counts as a number.
- Whenever nps_class gets a fractional score, it first rounds it to the nearest whole number with halves rounding up (6.5 becomes 7, -0.5 becomes 0).
- Whenever the rounded nps_class score is below 0 or above 10, it returns 'invalid'.
- Whenever the rounded nps_class score is 0 to 6, it returns 'detractor'.
- Whenever the rounded nps_class score is 7 or 8, it returns 'passive'.
- Whenever the rounded nps_class score is 9 or 10, it returns 'promoter'.
- Whenever split_bill gets a NULL or non-numeric total_cents or people, it returns NULL; numeric text counts as a number.
- Whenever split_bill gets a fractional people count, it drops the fraction toward zero first.
- Whenever split_bill has a people count below 1 after dropping the fraction (zero, negative, or between 0 and 1), it returns NULL.
- Whenever split_bill divides a total that does not split into whole cents, it rounds each share up to the next cent (toward positive infinity).
- Whenever split_bill gets a total_cents of zero, it returns 0; whenever the total is negative, it still divides and rounds toward positive infinity (a share of -33.3 becomes -33).
- Whenever mid_value gets values, it ignores NULLs and any value that is not numeric (numeric text counts as a number and is included).
- Whenever mid_value has no numeric values in the group (empty group or all ignored), it returns NULL.
- Whenever mid_value has an odd number of numeric values, it returns the middle one after sorting ascending.
- Whenever mid_value has an even number of numeric values, it returns the lower of the two middle values, not their average.
