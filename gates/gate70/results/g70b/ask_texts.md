# Gate 55 ask texts (gates/gate55/referee/review55.py)

## N0
There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## QN
The product owner is away until the morning. For every business decision a function's one-line spec leaves open (cut-offs and boundaries, rounding, minimums and caps, what happens with blank, missing, negative or oddly formatted input), record one question for him with `python3 /home/claude/hive/gates/gate70/referee/queue_question.py /home/claude/hive/runs/g70b/queue_QN.jsonl "<your question>"`, in plain business words, one decision per question; he will answer them all in the morning. Then build your best guess and keep going. Do not record a question a teammate has already recorded (`cat /home/claude/hive/runs/g70b/queue_QN.jsonl`). (`tools/ask.py` is not used on this project.)

## HV
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- charm_price: Whenever the raw price in cents is a positive number, the result is the lowest amount ending in 99 that is at or above it (for example 1 gives 99, 100 gives 199). A raw price of exactly 0 is not covered by this rule; see rule 3.
- charm_price: Whenever the raw price already ends in 99 (such as 99 or 199), the result is unchanged.
- charm_price: Whenever the raw price is 0 (a free item, including text that reads as 0, such as '0'), the result stays 0 and is not moved up to an amount ending in 99.
- charm_price: Whenever the raw price has a fraction (such as 150.5 or 0.5), it is first rounded up to the next whole cent and then moved up to the next amount ending in 99 (150.5 gives 199, 0.5 gives 99).
- charm_price: Whenever the raw price is negative (including -0.5), the result is the raw price unchanged (so -5 stays -5 and -0.5 stays -0.5). It is not rounded and not moved up to an amount ending in 99, and it is not NULL.
- charm_price: Whenever the raw price is NULL, empty text or text that is not a number, the result is NULL.
- charm_price: Whenever the raw price is text that reads as a number (such as '250', ' 250 ' or '1e3'), it is treated as that number, so '250' gives 299 and '1e3' gives 1099.
- charm_price: Whenever the raw price is very large, the result is still the next amount ending in 99 with no upper limit.
- tax_cents: Whenever a price in cents and a rate in basis points are given, the tax is price times rate divided by 10,000, rounded to whole cents (100 cents at 1000 bp gives 10; 1999 at 825 gives 165).
- tax_cents: Whenever the exact tax falls exactly halfway between two whole cents, it is rounded to the neighbouring whole cent that is even (half to even, not half away from zero): 10.5 becomes 10, 11.5 becomes 12 and 82.5 becomes 82. So 5 cents at 5000 bp gives 2, 25 cents at 5000 bp gives 12, and 1000 cents at 825 bp gives 82. For a negative tax the halfway case rounds to the even cent too, as in rule 12.
- tax_cents: Whenever the exact tax is below half a cent, it rounds down to 0 (1 cent at 4999 bp gives 0; 100 at 1 bp gives 0).
- tax_cents: Whenever the price is negative (a refund), the tax is the mirror image of the positive case, rounded half to even, so a refund of a halfway amount goes to the even cent and never away from zero (-5 at 5000 bp gives -2, -15 gives -8, -1000 at 825 bp gives -82, not -83).
- tax_cents: Whenever the rate is negative, the tax comes out negative by the same calculation (100 cents at -500 bp gives -5); a negative rate of less than half a cent in size gives 0.
- tax_cents: Whenever the price or the rate is 0, the tax is 0.
- tax_cents: Whenever the price or the rate is NULL, empty text or text that is not a number, the tax is NULL.
- tax_cents: Whenever the price or the rate is text that reads as a number (such as '100' and '1000'), it is used as that number.
- tax_cents: Whenever the price or rate has a fraction (10.5 cents, 12.5 bp), the exact value is used in the calculation and only the final tax is rounded, with halfway cases going to the even cent (100 at 12.5 bp gives 0; 10.5 at 1000 bp gives 1).
- grade_letter: Whenever the score is above scale_max, the grade is X (see rule 21). Otherwise, whenever the score is at least 90% of scale_max, the grade is A; at least 80% gives B; at least 70% gives C; at least 60% gives D; anything lower gives F.
- grade_letter: Whenever the score sits exactly on a cutoff (90, 80, 70 or 60 percent of scale_max), it gets the higher grade (90 of 100 is A, 60 of 100 is D, 27 of 30 is A).
- grade_letter: Whenever the score is just below a cutoff (89.99 of 100, 59.99 of 100), it gets the lower grade (B and F).
- grade_letter: Whenever the score is above scale_max (105 of 100, 150 of 100), the grade is X, even if the extra is bonus marks; a score exactly equal to scale_max is not above it and gets the normal grade (100 of 100 is A). Whenever the score is negative, the grade is F; there is no range check.
- grade_letter: Whenever the score is 0 with a valid scale (scale_max greater than 0), the grade is F.
- grade_letter: Whenever scale_max is 0 or negative, the grade is 'N/A', whatever the score is (a score of 0 on a scale_max of 0 gives 'N/A', not blank). This applies as long as scale_max is a number, including text that reads as a number.
- grade_letter: Whenever the score or scale_max is NULL, empty text or text that is not a number, the grade is NULL.
- grade_letter: Whenever the score or scale_max is text that reads as a number (such as '90', ' 90 ' or '100'), it is used as that number.
- grade_letter: Whenever scale_max is a fraction or a scale other than 100 (such as 10, 6 or 0.5), the percentages are applied to that scale (9 of 10 is A; 1 of 0.5 is A).
- loyalty_points: Whenever a purchase is made, the points are the number of full 100-cent blocks spent multiplied by the tier rate: 1 point per block for basic, 2 for silver and 3 for gold.
- loyalty_points: Whenever the spend is not a multiple of 100 cents, the leftover part is ignored with no rounding up (99 cents gives 0 points, 199 gold gives 3, 12345 gold gives 369).
- loyalty_points: Whenever the tier name is written in other letter case or with spaces around it (such as 'Gold', 'GOLD' or ' SILVER '), it is still recognised as that tier.
- loyalty_points: Whenever the tier is not basic, silver or gold (for example 'platinum', empty text or a number), it is treated as basic and earns 1 point per 100 cents.
- loyalty_points: Whenever the tier is NULL (missing), it is treated as basic and earns 1 point per 100 cents, the same as any tier that is not recognised. The result is not NULL because of a missing tier. For example, a NULL tier with 10000 cents spent gives 100 points.
- loyalty_points: Whenever the spend is 0 or negative, the points are 0, whatever the tier is, including a NULL tier.
- loyalty_points: Whenever the spend is NULL, empty text or text that is not a number, the result is NULL.
- loyalty_points: Whenever the spend is text that reads as a number (such as '12345', '250.5' or '1e3'), it is used as that number.
- loyalty_points: Whenever the spend has a fraction (such as 250.5 or 299.99), only the whole 100-cent blocks count (250.5 silver gives 4; 299.99 gold gives 6).
- mask_card: Whenever a card number has 8 or more digits and contains no letters, every digit except the last 4 is replaced by '*' and the last 4 digits are shown ('4111111111111111' gives '************1111', '12345678' gives '****5678').
- mask_card: Whenever the card number contains spaces, dashes, dots or any other non-digit characters that are not letters, those characters are removed and are not shown; only digits are counted and masked. Whenever the card number contains any letter anywhere in it (at the start, in the middle or at the end, however many digits it has), the card is rejected: no stars or digits are shown and the result is NULL, not the text 'INVALID' ('4111111111111111X' gives NULL, '4111 1111 1111 1111a' gives NULL, a 15-digit number with a stray letter at the end gives NULL). Non-Western digit characters are digits, not letters (see rule 43).
- mask_card: Whenever the card number has fewer than 8 digits (7 or fewer, including 4 digits or fewer), no stars or digits are shown and the result is the text 'INVALID' ('1234' gives 'INVALID', '123' gives 'INVALID', '1234567' gives 'INVALID').
- mask_card: Whenever the card number has no digits at all and contains no letters (empty text, text of zero length, or spaces and other non-letter characters only), it has fewer than 8 digits, so the result is the text 'INVALID'. It is never shown as empty text or left blank, and an empty card number is flagged the same way as any other card number with fewer than 8 digits. If it contains any letter, rule 37 applies and the result is NULL (letters only gives NULL).
- mask_card: Whenever the card number is NULL, the result is NULL.
- mask_card: Whenever the card number is given as a number rather than text, it is converted to digits first (4111111111111111 works as text); a whole-valued decimal such as 1234.0 is read as 1234, and a negative sign is dropped.
- mask_card: Whenever the card number is a number with a fraction, the decimal point is dropped and its digits are all counted as part of the card number. If that gives 8 or more digits it is masked like any other card number (1234567.5 gives '****5675'); if it gives fewer than 8 digits the result is 'INVALID' (12345.5 gives 'INVALID').
- mask_card: Whenever the card number contains non-Western digit characters (such as Arabic-Indic digits), they count as digits and are masked or shown like any other digit.
- mask_card: Whenever the card number has 8 or more digits of any length (8, 13, 16, 19 or more digits), the masked result has one '*' per digit hidden, so its length equals the number of digits.
- Whenever a parcel is shipped, the fee in cents is calculated as follows. Up to and including 250 g, the fee is a flat 300 in any zone. Above 250 g, the fee is the zone base plus the weight charge plus the overweight surcharge. The zone base is 500 for zone 1, 800 for zone 2 and 1200 for zone 3. An unknown zone pays 1200. The weight charge is 100 for each started kg after the first, so the first kg adds nothing. The overweight surcharge is 2500, added when the weight is over 30000 g.
- parcel_fee: Whenever the weight is over 250 g, it is charged per started 1000 g, not per 500 g. Each 1000 g block is priced as two 500 g units were before, so 500 g and 501 g in zone 1 both cost 500, and 1000 g in zone 1 is also 500. If the weight is a whole multiple of 1000 g, no extra block is charged. One gram more starts a new block (1001 g in zone 1 is 600, 1001 g in zone 3 is 1300).
- parcel_fee: Whenever the weight is above 0 g and up to 250 g (such as 1 g, 0.1 g or 250 g), one 500 g unit is charged, as before (zone 1 gives 400, zone 3 with 1 g gives 1000). The one exception is an unknown zone (see rule 49), where a weight in this range costs a flat 300. A weight of 0 g or less is not charged this unit; its fee is 0 (see rule 48).
- parcel_fee: Whenever the weight is zero or less (0 g, or any negative weight such as -1 g or -0.5 g), the fee is 0, not blank. This holds in any zone: zone 1, 2 or 3, an unknown zone (rule 49), and also when the zone is NULL. A negative weight is never left blank. The only weights that give a blank (NULL) fee are NULL, empty or non-numeric weights (rules 50 and 51).
- parcel_fee: Whenever the zone is anything other than 1, 2 or 3 (0, 4, 2.5, empty or non-numeric text), the zone is treated as an unknown zone. For an unknown zone, a weight above 0 g and up to 250 g (such as 1 g, 0.1 g or 250 g) costs a flat 300, so 1 g in zone 4 costs 300 and 250 g in zone 4 costs 300. Only a weight over 250 g gets the zone 3 rate: it is worked out exactly as it would be for zone 3, using the same weight rules, so 250.5 g in zone 4 costs the same as 250.5 g in zone 3, and 1001 g in zone 4 costs 1300. This does not apply when the zone is NULL (see rule 50): with a NULL zone the fee is still NULL for a weight above 0 g, and 0 for a weight of 0 g or less. The weight rules still come first: a weight of 0 g or less, including a negative weight, gives a fee of 0 (rule 48), and a NULL, empty or non-numeric weight gives NULL (rules 50 and 51).
- parcel_fee: Whenever the weight is NULL, the fee is NULL. Whenever the zone is NULL and the weight is above 0 g, the fee is NULL. A NULL zone does not hide a weight of 0 g or less: that still gives a fee of 0 (rule 48). A NULL weight gives NULL whatever the zone is.
- parcel_fee: Whenever the weight is empty text or text that is not a number, the fee is NULL.
- parcel_fee: Whenever the weight or the zone is text that reads as a number (such as '500', '2' or '1.0'), it is used as that number.
- parcel_fee: Whenever the weight has a fraction (250.5 g, 500.5 g), it counts as started weight. 250.5 g is over 250 g, so it is charged as a full 1000 g block: in zone 1, 250.5 g and 500.5 g both cost 500. There is no upper weight limit, so the fee has no cap. Whenever the weight is over 30 kg (30000 g, counting any fraction as started weight, so 30000.5 g is over and exactly 30000 g is not), a flat surcharge of 2500 (25.00 dollars) is added once on top of the normal block fee, in any zone, and it does not grow with the weight. In zone 1 the normal fee is 500 for the first 1000 g block plus 100 for each further block, so 100000 g in zone 1 is 10400 plus the 2500 surcharge, which is 12900. Weights of 30000 g or less have no surcharge. A weight of 0 g or less or a NULL or non-numeric weight still gives 0 or NULL as in rules 48, 50 and 51, with no surcharge. For an unknown zone, the surcharge is added to the zone 3 rate in the same way (rule 49).
- slugify: Whenever a title is given, the slug is the title in lower case with every run of characters other than letters a-z and digits 0-9 replaced by a single '-' (such as spaces, commas, ampersands, underscores and repeated dashes).
- slugify: Whenever the title starts or ends with spaces, punctuation or other separators, no leading or trailing '-' is left in the slug ('  Hello,   World!  ' gives 'hello-world').
- slugify: Whenever the title has accented letters (such as é, è, ï, ç, Ä, Ö, Ü), those letters are dropped without replacement. The base letter is not kept, and the dropped letter does not leave a separator behind, so the letters on either side stay joined. Spaces and other separators are still turned into '-' as usual ('Café Crème' gives 'caf-crme', 'naïve façade' gives 'nave-faade', 'Café Crème & Tea!' gives 'caf-crme-tea').
- slugify: Whenever the title has letters that are not plain a-z letters (such as ß, æ, Œ, accented letters like Ä, Ö, Ü, or Japanese characters), those characters are dropped without replacement, and they do not leave a separator behind. If nothing usable is left, the slug is 'untitled' ('ÄÖÜ ß' gives 'untitled', 'Œuvre æ' gives 'uvre').
- slugify: Whenever the title has compatibility characters such as full-width letters, superscript digits or Roman-numeral symbols, they are converted to plain letters and digits ('ｆｕｌｌ' gives 'full', 'x²' gives 'x2', 'Ⅻ' gives 'xii').
- slugify: Whenever the title has no usable letters or digits (empty text, text with only spaces or other separators, '***', only non-Latin characters such as Japanese, or only characters that get dropped), the slug is 'untitled', not empty text and not NULL. This applies even though the title was given and the other slug rules would leave nothing, so an empty title always gives 'untitled', never an empty web address.
- slugify: Whenever the title is NULL, the slug is NULL.
- slugify: Whenever the title is a number rather than text, it is turned into text first (123 gives '123', 1.5 gives '1-5'), and a whole-valued decimal such as 1.0 gives '1'.
- slugify: Whenever the title contains tabs or line breaks, they are treated like spaces and become a '-'; digits in the title are kept.
- slugify: Whenever two titles differ only by letter case or by the type of separator, they give the same slug; the slug is never made unique. Slugs over 40 characters are cut to the first 40, then any trailing hyphen is removed.
- ticket_priority: Whenever the severity is 1, 2, 3 or 4 and the ticket has been open less than 48 hours, the priority is P1, P2, P3 or P4 respectively.
- ticket_priority: Whenever the ticket has been open 48 hours or more, the priority is raised by one level (severity 4 gives P3, 3 gives P2, 2 gives P1); exactly 48 hours counts as escalated, and 47.9 hours does not.
- ticket_priority: Whenever a severity-1 ticket is open for any length of time, the priority stays P1; it cannot go above P1.
- Whenever the severity is a number that is not one of 1, 2, 3 or 4, the priority is NULL, whatever the hours open, with one exception: a whole-number severity above 4 (such as 5, 6 or 100, including text or a decimal that reads as one, like '5' or 5.0) is treated as severity 4, so it gets P4 when open less than 48 hours and P3 when open 48 hours or more, by the same rules as a severity-4 ticket. Severities such as 0, negative numbers, or fractions like 1.5 or 4.5 still give NULL.
- ticket_priority: Whenever the severity is NULL, empty text or text that is not a number, the priority is NULL.
- ticket_priority: Whenever the severity is text or a decimal that reads as one of 1 to 4 (such as '2' or 2.0), it is accepted as that severity.
- ticket_priority: Whenever the hours open is NULL, empty, not a number or negative, the open time is unusable, so the priority is NULL (blank), whatever the severity is. The ticket is not given a priority from the severity alone.
- ticket_priority: Whenever the hours open is text that reads as a number (such as '48', '  60 ' or '1e2'), it is used as that number for the 48-hour check.
- ticket_priority: Whenever the hours open is very large (there is no further escalation), the ticket is raised only one level, never more.
- workdays_between: Whenever the start date is before the end date, the result counts the Monday-to-Friday days from the start date up to but not including the end date, except that 25 December (Christmas Day) of any year is never counted, even when it falls on a weekday (2024-01-01 to 2024-01-08 gives 5; 2024-12-24 to 2024-12-26 gives 1).
- workdays_between: Whenever the start and end dates are the same, the result is 0.
- workdays_between: Whenever the start date is a weekday, that day is counted, unless it is 25 December (Christmas Day), which is never counted; whenever the end date is a weekday, it is not counted (2024-01-05 to 2024-01-06 gives 1; 2024-01-01 to 2024-01-02 gives 1; 2024-12-25 to 2024-12-26 gives 0).
- workdays_between: Whenever the start date falls on a Saturday or Sunday, that day is not counted (2024-01-06 to 2024-01-08 gives 0; 2024-01-06 to 2024-01-13 gives 5).
- workdays_between: Whenever the start date is after the end date (the dates are the wrong way round), the result is 0, not a negative number, and there is no error (2024-01-08 to 2024-01-01 gives 0; 2024-01-05 to 2024-01-01 gives 0).
- workdays_between: Whenever 25 December (Christmas Day) falls in the range, in any year, it is not counted, in the same way as Saturdays and Sundays are not counted (2024-12-24 to 2024-12-26 gives 1). Other public holidays are not excluded; apart from Christmas Day, only Saturdays and Sundays are skipped.
- workdays_between: Whenever either date is NULL, empty text or text that is not a date at all, the result is NULL. (A date in the right form that does not exist, such as 2024-02-30, is not covered by this rule; it gives -1 under rule 81.)
- workdays_between: Whenever either date is not in the exact form YYYY-MM-DD (such as '2024/01/01', '2024-1-1', or a number such as 20240101), the result is NULL. A date followed by a time of day is handled by rule 81, not this rule.
- workdays_between: Whenever either date (start or end) is in the right form YYYY-MM-DD but does not exist (such as 2024-02-30, 2023-02-29 or year 0000), the result is -1, not NULL and not an error; 2024-02-29 is accepted as a valid leap day. Whenever either date (start or end) is a date with a time of day added (such as '2024-01-01 10:00' or '2024-01-01T00:00'), it is not a valid date and the result is -1, not NULL and not an error.
- workdays_between: Whenever a date has spaces or line breaks before or after it (such as ' 2024-01-01 '), the surrounding whitespace is ignored and the date is accepted.
- workdays_between: Whenever the dates span a long period (such as a full year or from year 0001), the exact count of Monday-to-Friday days is returned, with 25 December of each year in the range left out even when it is a weekday (2024-01-01 to 2024-12-31 gives 260).
- median_amount: Whenever a group has an odd number of numeric values, the result is the middle value after sorting them from lowest to highest.
- median_amount: Whenever a group has an even number of numeric values, the result is the lower of the two middle values after sorting them from lowest to highest, with no averaging (1 and 2 give 1; 2.5 and 3.5 give 2.5; 1, 2, 3 and 4 give 2; 100 and 101 give 100).
- median_amount: Whenever a group contains NULL values, they are ignored and do not count toward the number of values.
- median_amount: Whenever a group contains text values, including text that looks like a number such as '5', they are ignored; only actual numbers are used.
- median_amount: Whenever a group has no numeric values at all (empty group, only NULLs or only text), the result is NULL.
- median_amount: Whenever the numeric values include whole numbers, decimals and negatives, they are all sorted by their numeric value together, and the median is then picked by the same rules as for any other numbers (an odd count gives the middle value; an even count gives the lower of the two middle values, with no averaging, so 1.5 and 2 give 1.5).
- median_amount: Whenever it is used with GROUP BY, each group gets its own median; without GROUP BY, one median covers all rows.
- median_amount: Whenever values repeat in a group, each repeat counts separately (1, 1, 1 and 5 give 1).
- ticket_priority: Whenever the severity is a number greater than 4 (such as 5, 6 or 10), including text or a decimal that reads as such a number (such as '5' or 5.0), it counts as severity 4. The priority is then worked out by the usual rules: P4 when the ticket has been open less than 48 hours, and P3 once it has been open 48 hours or more. If the hours open is NULL, empty, not a number or negative, the priority is NULL, as for any other severity. The priority is never blank because of the severity being above 4.
- A customer with orders of 5 and 1,000,000 and one order with no amount has a median of 500,002.5: the missing amount is skipped, so the two real orders are averaged. The owner says: No, it takes the lower of the two middle orders, so the median is 5, not 500,002.5.

## QA
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's answers
The team recorded these questions overnight and the owner answered them this morning. Build to his answers.

- Q: Working days between two dates: if the start date is after the end date, should the answer be 0, or a negative count?
  A: 0. If the end date is on or before the start date, return 0, not a negative count.
- Q: Working days between two dates: if either date is missing or not a valid YYYY-MM-DD date, should the answer be blank (NULL) or an error?
  A: Missing (NULL) start or end gives NULL. A date that's present but not a valid YYYY-MM-DD gives -1, not an error.
- Q: Working days: should public holidays ever be excluded, or only Saturdays and Sundays?
  A: Only one holiday: December 25 is excluded when it falls on a weekday. Otherwise just skip Saturdays and Sundays, no other public holidays.
- Q: Ticket priority: after how many hours open does a ticket move up one level (we assumed 48 hours), and can it move up more than one level (we assumed only one)?
  A: Yes, 48 hours or more moves it up one level. It's a single step only, so it never goes up more than one level, and never above P1.
- Q: Ticket priority: what should happen if severity is outside 1 to 4 or missing, or hours open is negative or missing? (We assumed: clamp severity into 1-4, blank if missing, negative hours count as 0.)
  A: Not quite. Severity outside 1–4 (0, negatives, above 4, fractions like 2.5) counts as 4, not clamped. Missing or non-numeric severity or hours returns NULL. Negative hours don't escalate, and 48+ hours escalates one level, up to P1.
- Q: Median of amounts: for an even number of values, should we average the two middle values (assumed), and should blank values be ignored (assumed)? What if the group has no values — blank?
  A: No averaging: for an even count, return the lower of the two middle values, keeping it as the original number. Yes, ignore blanks, NULLs and any non-numeric values, including text that looks like a number. If nothing numeric is left, return NULL.
- Q: Median of amounts: how should non-numeric text values in the group be treated — ignored, counted as 0, or an error?
  A: Ignored. Skip NULLs and any text, even if it looks like a number, and take the median of what's left.
- Q: Parcel fee: what is the full price table? We only know 1000g to zone 2 = 8.00, 1500g to zone 2 = 9.00 and 2500g to zone 3 = 14.00. What are the weight bands and prices for each zone (1, 2, 3)?
  A: Weight of 0 or less is 0. Over 0 up to 250 g is a flat 3.00 in every zone. Over 250 g, the base is 5.00 for zone 1, 8.00 for zone 2, and 12.00 for zone 3 (also used for a missing or unknown zone). Add 1.00 per started kg beyond the first kg, which is the weight rounded up to whole kg, minus 1. Over 30,000 g, add a flat 25.00. Exactly 30,000 g has no surcharge.

Your three examples match: 8.00, 9.00 and 14.00.
- Q: Parcel fee: what happens for a zone other than 1, 2 or 3 (e.g. 0, 4, blank)? We return no value (NULL).
  A: No, don't return NULL. For a weight over 250 g, any zone that isn't 1, 2 or 3 (0, 4, blank, text) gets the zone 3 base fee of 1200 cents. Up to 250 g it's the flat 300 regardless of zone.
- Q: Parcel fee: what is charged for a parcel weighing 0 g, a negative weight, or blank weight? We return no value for negative/blank and the lowest band for 0.
  A: Zero or negative weight should charge 0, not the lowest band. Blank weight returns no value (NULL), like you have it.
- Q: Parcel fee: is there a maximum weight we ship, or a cap on the fee, for very heavy parcels?
  A: No max weight and no cap on the fee. Over 30000 g just adds the flat 2500-cent surcharge, plus the usual 100 cents per started kg.
- Q: Parcel fee: is a weight exactly on a band edge (e.g. exactly 1000 g) charged at the lower band or the higher band?
  A: Exactly 1000 g gets the lower band. Extra kilograms are weight rounded up to whole kg, minus one, so 1000 g adds 0. 1000.5 g counts as 2 kg and adds 100 cents.
- Q: Slug: when a title has accented letters (e.g. 'Café Crème'), should they become plain letters (cafe-creme) or be dropped/split?
  A: Dropped, not converted or split. Non-ASCII characters get deleted outright with no separator, so 'Café Crème' becomes 'caf-crme'.
- Q: Slug: should a title that is blank or has no letters or digits (e.g. '!!!') give an empty slug or no value (NULL)? We return an empty slug; a blank/NULL title gives NULL.
  A: Neither: if the title ends up with no letters or digits, return 'untitled'. NULL in gives NULL, which you already do.
- Q: Slug: is there a maximum slug length, and should we cut at a whole word?
  A: Yes, max 40 characters. No, don't worry about whole words: just cut at 40 and drop any trailing hyphen left by the cut.
- Q: Slug: should an apostrophe split words ('don-t') as in the example, or can that change, and should '&' become 'and'? We follow the example and drop '&'.
  A: Yes, an apostrophe splits words, so "don't" becomes "don-t". That's the rule for any non-a-z/0-9 character. Dropping '&' is right too: it becomes a hyphen like other punctuation, not "and".
- Q: Shelf price: when a raw price already ends in 99 we keep it, otherwise we round UP to the next price ending in 99 (e.g. 1200 becomes 1299). Is rounding up always right, even for tiny prices like 50 cents (becomes 99)?
  A: No. Anything under 100 cents stays as it is, so 50 stays 50 and only prices of 100 or more get rounded up to the next 99.
- Q: Shelf price: what should a zero or negative raw price give? My guess: 0 gives 99, negative gives blank (NULL).
  A: Both come back unchanged: anything under 100 cents, including 0 and negatives, is returned as is. So 0 stays 0 and a negative stays negative, with no 99 and no NULL.
- Q: Letter grades: what are the percentage cut-offs? My guess: 90% and above A, 80 B, 70 C, 60 D, below 60 F, with the boundary percentage itself earning the higher grade.
  A: Yes, that's right, with one detail. Round the percentage half up to a whole number first, so 89.5% counts as 90% and gets an A, while 89.4% rounds to 89% and gets a B.
- Q: Letter grades: for a score above the scale maximum, or below zero, or a scale maximum of zero or less, what do we show? My guess: above max is A, below zero is F, bad scale gives blank (NULL).
  A: Not quite. Above max is 'X', not A. Below zero is F, as you guessed. A scale max of zero or less shows 'N/A', not blank. Blank (NULL) is only for a missing or non-numeric score or scale max.
- Q: Sales tax: when the tax lands exactly halfway between two cents, do we round up? My guess: yes, half a cent rounds up (away from zero for refunds/negative prices).
  A: No, exact halves go to the nearest even cent (10.5 becomes 10, 11.5 becomes 12). Negative prices work the same way, just with a negative sign.
- Q: Sales tax: how should a negative price (refund) or a negative rate behave? My guess: tax is computed the same way and comes out negative.
  A: Yes, your guess is right. A negative price gives a negative tax, rounded half-to-even on the positive amount. A negative rate is not capped, so it gives a negative result. The 3000 bp cap only applies to rates above it.
- Q: Loyalty points: my guess is basic earns 1 point per whole 100 cents spent, silver 2, gold 3, with leftover cents ignored. Is that right, and is there a cap or minimum purchase?
  A: Yes, that's right. Cap is 5000 points max, and anything under 100 cents earns 0.
- Q: Loyalty points: what happens with an unknown, blank or missing tier name, and is the tier name case-insensitive? My guess: ignore case and spaces; unknown or blank tier earns at the basic rate; missing spend gives blank.
  A: Yes, tier name ignores case and spaces. Unknown, blank, or missing tier gets the basic rate of 1 point per unit. Missing spend is different: it returns 0, not blank.
- Q: Loyalty points: what should a zero or negative spend (e.g. a refund) earn? My guess: zero points, never negative.
  A: Yes, zero points, never negative. Any spend of zero or less, like a refund, earns 0.
- Q: Card masking: my guess is we hide all digits except the last 4, drop spaces and dashes, and show stars only. For numbers with fewer than 4 digits, do we hide everything? My guess: yes.
  A: No. With fewer than 8 digits it returns the text 'INVALID' rather than masking. Masking only happens at 8 or more digits, and then it's stars for all but the last four.
- Q: Card masking: a blank card number gives blank text and a missing one gives NULL; letters in the number are dropped like dashes. OK?
  A: Not quite. A missing number gives NULL, but a blank one gives 'INVALID'. Letters aren't dropped. Any letter makes the whole result NULL. Only spaces and hyphens get stripped.
- Q: Parcel fee: from the examples I infer a base fee of 300 cents times the zone number plus 100 cents for every started 500 grams. Is that the real rate card, and is there a minimum or maximum fee?
  A: No, that's not the rate card. Up to 250 g it's a flat 300 cents. Above that the base is 500, 800 or 1200 cents for zones 1, 2 and 3, and anything unknown uses 1200. Add 100 cents for each started kilogram beyond the first, and 2500 cents extra above 30000 g. Weight of zero or less is 0. There's no other minimum or maximum.
- Q: Parcel fee: what should a zero-gram parcel cost (my guess: just the zone base fee), and what about a negative or missing weight (my guess: blank/NULL)?
  A: Zero or negative weight costs 0, whatever the zone. A missing or non-numeric weight returns NULL, so you're right on that one.
- Q: Parcel fee: for a zone other than 1, 2 or 3 (or a missing zone) do we show blank (NULL)? Is there a weight limit above which we refuse to quote?
  A: No, don't blank it. An unknown or missing zone just gets the zone 3 rate (1200 base) when the parcel is over 250 g. Under 250 g it's the flat 300 anyway. No weight limit: we always quote, and anything over 30000 g just gets a 2500 cent surcharge on top.
- Q: Slugs: should accented letters be turned into plain ones (e.g. Café becomes cafe) or dropped/separated? My guess: accents are stripped to the plain letter, other non-English characters act as separators.
  A: Neither. Delete every non-ASCII character outright, with no separator, so Café becomes "caf".
- Q: Slugs: a title with no letters or digits gives an empty slug, a missing title gives NULL, and there is no maximum slug length. OK?
  A: Not quite: the empty slug should return 'untitled', not empty. NULL title gives NULL, that's right. Also cap slugs at 40 characters, then drop any trailing hyphen left by the cut.
