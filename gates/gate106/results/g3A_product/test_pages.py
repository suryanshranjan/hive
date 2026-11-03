import pathlib
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
def test_invite_500_shown_before_button():
    s = page('invite.html'); assert '₹500' in s and s.index('₹500') < s.index('<button')
def test_invite_reward_not_pushed_down():
    assert 'margin-top:400px' not in page('invite.html')
def test_invite_has_whatsapp_and_ref_link():
    s = page('invite.html'); assert 'wa.me' in s and 'signup.html?ref=' in s
def test_invite_copy_uses_clipboard():
    assert 'clipboard' in page('invite.html')
def test_invite_link_input_readonly():
    s = page('invite.html'); assert 'id="invite-link"' in s and 'readonly' in s
def test_invite_whatsapp_above_copy_button():
    s = page('invite.html'); assert s.index('Share on WhatsApp') < s.index('Copy invite link</button>')
def test_dashboard_links_to_invite():
    assert 'href="invite.html"' in page('dashboard.html')
def test_dashboard_links_to_deals():
    assert 'href="deals.html"' in page('dashboard.html')
def test_dashboard_no_empty_state():
    assert 'No data.' not in page('dashboard.html')
def test_deals_links_to_invite():
    assert 'href="invite.html"' in page('deals.html')
def test_nav_links_to_deals_and_invite():
    for n in ('index.html', 'signup.html', 'dashboard.html', 'deals.html', 'invite.html'):
        s = page(n); nav = s[s.index('<nav'):s.index('</nav>')]
        assert 'href="deals.html"' in nav and 'href="invite.html"' in nav, n
import re
def _input(s, name):
    return re.search(r'<input[^>]*name="%s"[^>]*>' % name, s).group(0)
def test_signup_gst_not_required():
    assert 'required' not in _input(page('signup.html'), 'gst')
def test_signup_bank_fields_not_required():
    s = page('signup.html')
    assert 'required' not in _input(s, 'account') and 'required' not in _input(s, 'ifsc')
def test_signup_has_ref_field():
    s = page('signup.html'); assert 'name="ref"' in s and "get('ref')" in s
def test_signup_form_action_dashboard():
    assert 'action="dashboard.html"' in page('signup.html')
def test_signup_only_four_required_fields():
    s = page('signup.html')
    req = sorted(re.search(r'name="(\w+)"', t).group(1) for t in re.findall(r'<input[^>]*required[^>]*>', s))
    assert req == ['email', 'instagram', 'name', 'phone']
def test_signup_payout_section_and_copy():
    s = page('signup.html')
    assert 'Payout details (needed before your first payout, you can add these later)' in s
    assert 'Join Sunny Shop as a creator' in s and 'Join and see deals' in s
    assert s.index('Payout details') < s.index('name="pan"')
def test_signup_welcomes_invited_friend():
    s = page('signup.html')
    assert 'Your friend invited you. Finish your first deal and you both get ₹500.' in s
    assert 'id="invite-banner"' in s and 'hidden' in s.split('id="invite-banner"')[1].split('>')[0]
    assert "getElementById('invite-banner').hidden = false" in s
def test_signup_shows_real_deal_examples_above_form():
    s = page('signup.html'); top = s[:s.index('<form')]
    assert '₹500' in top and 'Chai Co ₹3,000 for 2 reels' in top and 'FitBottle ₹2,000 for 3 stories' in top
def test_signup_shows_8000_average():
    s = page('signup.html'); assert '₹8,000 a month' in s[:s.index('<form')]
