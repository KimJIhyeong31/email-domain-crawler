import customtkinter as ctk
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
import re
import threading
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ======================== 전역 변수 ========================
visited = set()                # 방문한 URL 저장
found_page = None              # 타겟 도메인을 찾은 페이지 URL
found_via_mailto = False       # mailto 링크에서 발견 여부
other_domains = dict()         # 발견된 전체 도메인: {도메인: URL}
mailto_links = []              # 발견된 mailto 링크: [(mailto주소, 출처 URL)]

# ======================== GUI 설정 ========================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("이메일도메인 검색")
app.geometry("500x450+900+500")

# Start URL 라벨 및 입력
label1 = ctk.CTkLabel(app, text="  공식웹사이트 주소 입력", font=("맑은 고딕", 15), anchor="w", width=460)
label1.pack(pady=(12, 0))
entry_url = ctk.CTkEntry(app, placeholder_text="https://www.example.com", width=460, height=40, font=("맑은 고딕", 14))
entry_url.pack(pady=5)

# Target Domain 라벨 및 입력
label2 = ctk.CTkLabel(app, text="  이메일도메인 주소 입력", font=("맑은 고딕", 15), anchor="w", width=460)
label2.pack(pady=(12, 0))
entry_domain = ctk.CTkEntry(app, placeholder_text="@example.com", width=460, height=40, font=("맑은 고딕", 14))
entry_domain.pack(pady=5)

# 결과 메시지
result_label = ctk.CTkLabel(app, text="", font=("맑은 고딕", 14), text_color="lightgray", width=460)
result_label.pack(pady=(15, 5))

# 검색 도메인 텍스트 박스
label_other = ctk.CTkLabel(app, text="검색된 모든 이메일도메인, URL :", font=("맑은 고딕", 14), anchor="w", width=460)
label_other.pack(pady=(12, 0))
text_other = ctk.CTkTextbox(app, width=460, height=120, font=("맑은 고딕", 13))
text_other.pack(pady=5)

# ======================== 도메인 자동 채우기 ========================
def update_domain_default(event=None):
    url = entry_url.get().strip()
    if not url:
        return
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    if domain:
        entry_domain.delete(0, 'end')
        entry_domain.insert(0, f"@{domain}")

entry_url.bind("<FocusOut>", update_domain_default)

# ======================== 내부링크 판별 ========================
def is_internal_link(base_url, link):
    if not link:
        return False
    parsed_base = urlparse(base_url)
    parsed_link = urlparse(link)
    exclude_schemes = ('mailto', 'javascript', 'tel', 'data')
    if parsed_link.scheme in exclude_schemes:
        return False
    if link.strip().startswith('#') or parsed_link.path.endswith(('.pdf', '.zip', '.exe')):
        return False
    return parsed_base.netloc == parsed_link.netloc

# ======================== 크롤링 함수 ========================
def crawl(url, target_domain):
    global found_page, found_via_mailto
    if url in visited or found_page:
        return
    visited.add(url)

    def update_status():
        result_label.configure(text=f"🔍 검색 중: {url}", text_color="lightblue")
        app.update_idletasks()
    app.after(0, update_status)

    try:
        res = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/114.0.0.0 Safari/537.36"
                )
            },
            timeout=10
        )
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')

        text = soup.get_text()
        found_emails = set(re.findall(r'@[\w.-]+\.\w+\b', text))
        for em in found_emails:
            if em not in other_domains:
                other_domains[em] = url

        # 텍스트에서 이메일 도메인 검색
        if target_domain.lower() in text.lower():
            found_page = url
            return

        # mailto 링크 수집
        a_tags = soup.find_all('a', href=True)
        for a_tag in a_tags:
            href = a_tag['href'].strip().lower()
            if href.startswith("mailto:"):
                full_url = urljoin(url, href)
                if (full_url, url) not in mailto_links:
                    mailto_links.append((full_url, url))

        # 링크 버킷: 우선순위 기반 분류
        buckets = {1: [], 2: [], 3: [], 4: [], 5: [], 7: []}
        for a_tag in a_tags:
            href = a_tag['href'].strip()
            text_a = a_tag.get_text(strip=True).lower()
            full_url = urljoin(url, href)
            href_lower = href.lower()
            if (href_lower.startswith(('mailto:', 'javascript:', 'tel:', 'data:', '#'))
                or a_tag.has_attr("download")):
                continue
            if 'privacy' in href_lower or 'privacy' in text_a or '개인정보' in text_a:
                buckets[1].append(full_url)
            elif 'terms' in href_lower or 'terms' in text_a or '이용약관' in text_a:
                buckets[2].append(full_url)
            elif any(k in href_lower for k in ['support', 'help', 'service']) or '고객' in text_a:
                buckets[3].append(full_url)
            elif any(k in href_lower for k in ['notice', 'news', 'announcement']) or '공지' in text_a:
                buckets[4].append(full_url)
            elif any(k in href_lower for k in ['recruit', 'career', 'job']) or '차용' in text_a:
                buckets[5].append(full_url)
            else:
                buckets[7].append(full_url)

        # 내부 링크 재귀 크롤링
        for i in [1, 2, 3, 4, 5, 7]:
            for link in buckets[i]:
                if is_internal_link(url, link):
                    crawl(link, target_domain)
                    if found_page:
                        return

        # 마지막 수단: mailto 검사
        for mailto_url, source_url in mailto_links:
            email = mailto_url[len("mailto:"):].split('?')[0].strip()
            if target_domain.lower() in email.lower():
                found_page = source_url
                found_via_mailto = True
                return


    except Exception as e:
        err_msg = f"❗ 오류 발생: {str(e)}"
        app.after(0, lambda: result_label.configure(text=err_msg, text_color="orange"))

# ======================== Selenium 캡처 ========================
def selenium_highlight(target_url, target_domain):
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(target_url)
    time.sleep(2)

    # 페이지 내 도메인 텍스트를 하이라이팅하는 JavaScript
    highlight_script = f"""
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
    let node;
    let found = false;

    while (node = walker.nextNode()) {{
        const text = node.nodeValue;
        const index = text.indexOf("{target_domain}");
        if (index !== -1) {{
            const span = document.createElement('span');
            span.style.backgroundColor = 'yellow';

            const before = document.createTextNode(text.slice(0, index));
            const highlight = document.createTextNode(text.slice(index, index + "{target_domain}".length));
            const after = document.createTextNode(text.slice(index + "{target_domain}".length));

            span.appendChild(highlight);

            const parent = node.parentNode;
            parent.insertBefore(before, node);
            parent.insertBefore(span, node);
            parent.insertBefore(after, node);
            parent.removeChild(node);

            span.scrollIntoView({{ behavior: "auto", block: "center" }});
            found = true;
            break;
        }}
    }}
    return found;
    """
    found = driver.execute_script(highlight_script)
    if found:
        time.sleep(2)
        save_name = f"{target_domain.replace('@', 'at_').replace('.', '_')}.png"
        driver.save_screenshot(save_name)
    driver.quit()
    return found

# ======================== 도메인 목록 실시간 출력 ========================
def update_other_domains():
    text_other.configure(state="normal")
    text_other.delete("1.0", "end")
    for dom in sorted(other_domains.keys()):
        url = other_domains[dom]
        text_other.insert("end", f"{dom}  URL : {url}\n")
    text_other.configure(state="disabled")
    app.after(3000, update_other_domains)

# ======================== 버튼 클릭 이벤트 ========================
def on_click():
    global visited, found_page, found_via_mailto, other_domains, mailto_links
    visited, other_domains, mailto_links = set(), dict(), []
    found_page = None
    found_via_mailto = False

    start_url = entry_url.get().strip()
    target_domain = entry_domain.get().strip()

    if not start_url or not target_domain:
        result_label.configure(text="❗ 공식 웹사이트 주소와 도메인을 '모두' 입력해주세요.", text_color="orange")
        return

    def run():
        result_label.configure(text="🔍 검색 중입니다. 잠시만 기다려주세요.", text_color="lightblue")
        app.update_idletasks()
        crawl(start_url, target_domain)

        if found_page:
            if found_via_mailto:
                result_label.configure(text=f"✅ mailto 링크에서 도메인을 찾았습니다!\n{found_page}", text_color="lightgreen")
            else:
                result_label.configure(text=f"✅ 도메인 포함 페이지를 찾았습니다!\n{found_page}", text_color="lightgreen")
                result_label.configure(text="🔎 도메인 캡처 사전 준비 중", text_color="lightblue")
                app.update_idletasks()
                success = selenium_highlight(found_page, target_domain)
                if success:
                    result_label.configure(text="📸 도메인 캡처 완료!", text_color="lightgreen")
                else:
                    result_label.configure(text="❗ 도메인 텍스트를 찾지 못했습니다 (Selenium).", text_color="red")
        else:
            result_label.configure(text="❌ 도메인을 찾지 못했습니다.", text_color="red")

    threading.Thread(target=run, daemon=True).start()

# ======================== 버튼 UI ========================
btn_frame = ctk.CTkFrame(app, fg_color="transparent")
btn_frame.pack(pady=(7, 0))

# 확인 버튼
btn_confirm = ctk.CTkButton(
    btn_frame,
    text="확인",
    command=on_click,
    width=120,
    height=35,
    font=("맑은 고딕", 14),
    text_color="white",
    corner_radius=10
)
btn_confirm.grid(row=0, column=0, padx=10)

# 종료 버튼
btn_exit = ctk.CTkButton(
    btn_frame,
    text="종료",
    command=app.destroy,
    width=120,
    height=35,
    font=("맑은 고딕", 14),
    text_color="black",
    fg_color="gray",
    corner_radius=10
)
btn_exit.grid(row=0, column=1, padx=10)
# ======================== 실시간 출력 시작 ========================
update_other_domains()
app.mainloop()
