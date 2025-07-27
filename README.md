readme_content = """
# 이메일 도메인 크롤러 (Email Domain Crawler)

사용자가 입력한 공식 웹사이트를 재귀적으로 탐색하여 식별대상 이메일도메인이 포함된 페이지를 찾아내고,  
발견 시 Selenium으로 해당 위치를 하이라이팅하고 스크린샷까지 저장하는 Python GUI 프로그램입니다.

---

## 주요 기능

- 공식 웹사이트 내부 링크를 따라가며 이메일 도메인 포함 여부 크롤링
- 내부링크 탐색 우선순위 설정 : 개인정보처리방침-이용약관-고객센터-공지사항-채용-기타 순으로 순차 탐색
- `mailto:` 링크까지 검사하여 이메일 도메인 존재 여부 확인,
  mailto 링크만 별도로 관리, 타 링크에서 도메인 미검색 시 mailto 링크에서 최종 검색
- 이메일 도메인 텍스트를 페이지에서 노란색 하이라이트 처리 (Selenium 사용)
- 하이라이트된 페이지 스크린샷 자동 저장
- GUI 제공 (CustomTkinter 기반)
- 검색된 모든 이메일 도메인과 해당 URL 실시간으로 출력

---

## 사용 기술

- Python 3.x
- requests
- beautifulsoup4
- selenium
- webdriver-manager
- customtkinter
- re, threading, time (표준 라이브러리)

---

## 설치 방법

1. Python 3.x 설치 ([공식 사이트](https://www.python.org/downloads/))

2. 의존 패키지 설치 (터미널 또는 CMD에서 프로젝트 폴더로 이동 후):

    ```bash
    pip install -r requirements.txt
    ```

---

## 사용 방법

1. 프로그램 실행 (`main.py` 실행)

2. 공식 웹사이트 URL 입력 (예: `https://www.example.com`)

3. 이메일도메인 입력 (예: `@example.com`)

4. '확인' 버튼 클릭

5. 크롤링 진행 및 결과 확인  
   - 도메인 포함 페이지 발견 시 Selenium이 페이지를 열어 하이라이트하고 캡처  
   - mailto 링크에서 도메인 찾으면 별도 안내 - url만 출력, 캡처 불가  
   - 찾지 못하면 실패 메시지 출력

6. 검색된 모든 이메일 도메인과 URL은 하단 텍스트 박스에서 실시간 확인 가능

---

## 파일 구성

email-domain-crawler/
│
├── main.py # 메인 실행 코드
├── README.md # 당해 설명서
├── requirements.txt # 필요한 패키지 목록
└── screenshot.png # 실행 화면 캡처 이미지


---

## 앞으로 개선할 점 (TODO)

- 크롤링 속도 최적화 및 중복 도메인 제거 기능 강화
- 다중 이메일 도메인 입력 기능 추가
- 크롤링 시간 및 상태 표시 개선
- 결과 데이터를 CSV 등 파일로 저장하는 기능 추가


---

> 이 프로그램은 삼일회계법인 디지털 전형 과제를 위해 개발된 개인 프로젝트입니다.  
> 작성자: 김지형  

---

📦 GitHub Repository  
https://github.com/KimJIhyeong31/email-domain-crawler
