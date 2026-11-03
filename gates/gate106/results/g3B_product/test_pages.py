import pathlib
import re
D = pathlib.Path(__file__).parent
page = lambda n: (D / n).read_text(encoding='utf-8')
def test_pages_exist():
    for n in ('index.html', 'signup.html', 'dashboard.html', 'deals.html', 'invite.html', 'terms.html'):
        assert (D / n).exists()
def test_signup_collects_email_and_instagram():
    s = page('signup.html'); assert 'name="email"' in s and 'name="instagram"' in s
def test_signup_goes_to_dashboard():
    assert 'dashboard.html' in page('signup.html')
def test_deals_listed():
    assert page('deals.html').count('<li') >= 3
def test_invite_reward_is_500():
    assert '₹500' in page('invite.html')
def test_invite_has_whatsapp_share():
    s = page('invite.html'); assert 'wa.me' in s and 'Share on WhatsApp' in s
def test_invite_builds_ref_link():
    s = page('invite.html'); assert 'ref=' in s and 'sunny_ref' in s and 'signup.html' in s
def test_invite_reward_not_hidden():
    s = page('invite.html'); assert 'margin-top:400px' not in s and 'font-size:12px' not in s
def test_invite_headline_and_copy():
    s = page('invite.html')
    assert 'Invite a friend, you both get ₹500' in s
    assert 'navigator.clipboard.writeText' in s and 'Copied!' in s
    assert s.index('Share on WhatsApp') < s.index('readonly') < s.index('Copy invite link')
def test_signup_carries_invite_ref():
    s = page('signup.html')
    assert 'name="ref"' in s and "A friend invited you: you'll both get ₹500 after your first deal" in s
def test_signup_payout_details_optional():
    s = page('signup.html')
    for n in ('pan', 'gst', 'account', 'ifsc', 'address'):
        tag = re.search(r'<input[^>]*name="%s"[^>]*>' % n, s)
        assert tag is None or 'required' not in tag.group(0)
    assert re.search(r'<input[^>]*name="gst"[^>]*>', s) and 'Needed before your first payout, you can add later' in s
def test_signup_short_form_copy():
    s = page('signup.html')
    assert 'Join Sunny Shop and get paid for Instagram posts' in s and 'Brands pay ₹1,500–₹3,000 per deal' in s
    assert 'Join and see deals' in s and 'as on PAN' not in s
    for n in ('name', 'email', 'phone', 'instagram'):
        assert re.search(r'<input[^>]*name="%s"[^>]*required' % n, s)
def test_dashboard_leads_to_first_deal_then_invite():
    s = page('dashboard.html'); assert 'No data.' not in s
    body = s.split('</nav>', 1)[1]
    assert 'deals.html' in body and 'invite.html' in body
    assert body.index('deals.html') < body.index('invite.html')
    assert 'Find your first deal: brands pay ₹1,500–₹3,000' in body
    assert 'Invite a friend, you both get ₹500 after their first deal' in body
def test_nav_links_on_product_pages():
    for n in ('dashboard.html', 'deals.html', 'invite.html'):
        nav = re.search(r'<nav>.*?</nav>', page(n), re.S).group(0)
        for h in ('deals.html', 'invite.html', 'dashboard.html'):
            assert 'href="%s"' % h in nav
        assert 'Invite &amp; earn ₹500' in nav
def test_deals_points_to_invite():
    s = page('deals.html'); assert 'invite.html' in s
    assert "Know a creator who'd like these? Invite them, you both get ₹500" in s
