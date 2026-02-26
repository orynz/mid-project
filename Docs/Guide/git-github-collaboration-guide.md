# 🤝 Git & GitHub 협업 완벽 가이드

> 개인 사용 경험을 바탕으로 팀 협업으로 전환하는 단계별 총정리

---

## 📋 목차
1. [협업 vs 개인 사용의 차이](#협업-vs-개인-사용의-차이)
2. [협업 워크플로우 전체 흐름](#협업-워크플로우-전체-흐름)
3. [초기 설정](#초기-설정)
4. [브랜치 전략](#브랜치-전략)
5. [단계별 협업 프로세스](#단계별-협업-프로세스)
6. [Pull Request (PR) 가이드](#pull-request-pr-가이드)
7. [충돌(Conflict) 해결](#충돌conflict-해결)
8. [자주 사용하는 명령어 총정리](#자주-사용하는-명령어-총정리)
9. [주의사항 & 협업 에티켓](#주의사항--협업-에티켓)
10. [긴급 상황 대처법](#긴급-상황-대처법)

---

## 협업 vs 개인 사용의 차이

| 항목 | 개인 사용 | 협업 |
|------|-----------|------|
| 브랜치 | main 하나로 작업 | 기능별 브랜치 분리 |
| push | 바로 main에 push | PR(Pull Request)을 통해 merge |
| 커밋 메시지 | 자유롭게 작성 | 컨벤션에 따라 통일 |
| 코드 리뷰 | 없음 | 필수 |
| 충돌 | 거의 발생 안 함 | 자주 발생, 해결 능력 필요 |

---

## 협업 워크플로우 전체 흐름

```
[원격 저장소 fork/clone]
        ↓
[로컬에서 브랜치 생성]
        ↓
[기능 개발 & 커밋]
        ↓
[원격 저장소에 push]
        ↓
[Pull Request 생성]
        ↓
[코드 리뷰 & 수정]
        ↓
[main 브랜치에 merge]
        ↓
[로컬 main 업데이트 & 브랜치 삭제]
```

---

## 초기 설정

### 1. Git 기본 설정 (최초 1회)

```bash
# 이름 & 이메일 설정 (커밋에 표시됨)
git config --global user.name "홍길동"
git config --global user.email "hong@example.com"

# 기본 브랜치 이름을 main으로 설정
git config --global init.defaultBranch main

# 설정 확인
git config --list
```

### 2. 저장소 시작 방법 (2가지 중 선택)

#### 방법 A: 팀원이 만든 저장소를 클론

```bash
# 원격 저장소 복제
git clone https://github.com/팀/저장소이름.git

# 클론한 폴더로 이동
cd 저장소이름
```

#### 방법 B: 오픈소스 프로젝트 기여 (Fork 방식)

```bash
# 1. GitHub에서 Fork 버튼 클릭 → 내 계정에 복사
# 2. 내 포크를 클론
git clone https://github.com/내계정/저장소이름.git

# 3. 원본 저장소를 upstream으로 추가
git remote add upstream https://github.com/원본팀/저장소이름.git

# 4. 리모트 확인
git remote -v
# origin   https://github.com/내계정/저장소이름.git (fetch/push)
# upstream https://github.com/원본팀/저장소이름.git (fetch/push)
```

---

## 브랜치 전략

### GitHub Flow (소규모 팀 권장)

```
main ─────────────────────────────────────────▶
         │                           │
         └─ feature/login ──────────┘ (merge)
                   └─ fix/login-bug ┘ (merge)
```

- `main`: 항상 배포 가능한 안정적인 상태
- `feature/기능명`: 새 기능 개발
- `fix/버그명`: 버그 수정
- `hotfix/긴급수정`: 긴급 패치

### Git Flow (대규모 팀)

```
main       ────────────────────────────────────▶ (배포)
develop    ──────────────────────────────────▶ (통합)
              │              │
              └─ feature/A ──┘
                    └─ feature/B ──┘
```

> **초보자 추천**: GitHub Flow (더 단순함)

### 브랜치 이름 규칙 예시

```
feature/user-login       # 새 기능
feature/payment-module
fix/login-error          # 버그 수정
fix/null-pointer-crash
hotfix/security-patch    # 긴급 수정
docs/api-documentation   # 문서
refactor/database-query  # 리팩토링
```

---

## 단계별 협업 프로세스

### STEP 1: 작업 시작 전 — 최신 코드 받기

```bash
# main 브랜치로 이동
git checkout main

# 원격의 최신 변경사항 가져오기
git pull origin main

# (Fork 방식이라면)
git fetch upstream
git merge upstream/main
```

⚠️ **작업 시작 전 반드시 pull 먼저!** 안 하면 충돌 위험 증가

---

### STEP 2: 브랜치 생성

```bash
# 브랜치 생성 + 이동 (한 번에)
git checkout -b feature/로그인기능

# 또는 최신 방식
git switch -c feature/로그인기능

# 현재 브랜치 확인
git branch
```

---

### STEP 3: 개발 & 커밋

```bash
# 변경 파일 확인
git status

# 특정 파일만 스테이징
git add src/login.js

# 전체 변경사항 스테이징 (주의: 불필요한 파일 포함될 수 있음)
git add .

# 커밋 (메시지 규칙 중요!)
git commit -m "feat: 로그인 폼 UI 구현"
```

### 커밋 메시지 규칙 (Conventional Commits)

```
타입: 제목 (50자 이내)

본문 (선택사항, 왜 변경했는지 설명)

Closes #이슈번호
```

| 타입 | 사용 상황 |
|------|-----------|
| `feat` | 새 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서 변경 |
| `style` | 코드 형식 변경 (기능 변화 없음) |
| `refactor` | 리팩토링 |
| `test` | 테스트 추가/수정 |
| `chore` | 빌드, 설정 파일 변경 |

```bash
# 좋은 커밋 메시지 예시
git commit -m "feat: 소셜 로그인 Google OAuth 연동"
git commit -m "fix: 로그인 실패 시 에러 메시지 미표시 버그 수정"
git commit -m "docs: README에 환경변수 설정 방법 추가"

# 나쁜 커밋 메시지 예시 ❌
git commit -m "수정"
git commit -m "asdf"
git commit -m "작업중"
```

---

### STEP 4: 원격 저장소에 Push

```bash
# 처음 push (브랜치를 원격에 등록)
git push -u origin feature/로그인기능

# 이후 push
git push

# push 전에 최신 상태 반영하기 (충돌 예방)
git pull origin main --rebase
git push origin feature/로그인기능
```

---

### STEP 5: Pull Request 생성 (GitHub에서)

1. GitHub 저장소 접속
2. `Compare & pull request` 버튼 클릭
3. PR 제목과 설명 작성
4. 리뷰어(Reviewer) 지정
5. `Create pull request` 클릭

---

### STEP 6: 코드 리뷰 대응

```bash
# 리뷰어 피드백을 받았다면 로컬에서 수정 후
git add .
git commit -m "fix: 리뷰 반영 - 입력값 유효성 검사 추가"
git push

# PR은 자동으로 업데이트됨
```

---

### STEP 7: Merge 완료 후 정리

```bash
# main 브랜치로 이동
git checkout main

# 최신 코드 받기
git pull origin main

# 사용 완료된 로컬 브랜치 삭제
git branch -d feature/로그인기능

# 원격 브랜치 삭제 (GitHub에서 자동 삭제 설정 가능)
git push origin --delete feature/로그인기능
```

---

## Pull Request (PR) 가이드

### PR 설명 템플릿

```markdown
## 작업 내용
- Google OAuth 로그인 버튼 추가
- 로그인 성공/실패 처리 로직 구현
- 에러 메시지 UI 추가

## 변경 이유
기존에 이메일 로그인만 지원하여 사용자 편의성이 낮았음

## 테스트 방법
1. 로컬 서버 실행
2. /login 페이지 접속
3. Google 로그인 버튼 클릭

## 관련 이슈
Closes #42

## 스크린샷 (UI 변경 시)
[이미지 첨부]
```

### 코드 리뷰 할 때 주석 규칙

```
[필수] 반드시 수정해야 함
[제안] 수정하면 좋겠음
[질문] 이렇게 한 이유가 있나요?
[칭찬] 이 부분 잘 구현했네요!
```

---

## 충돌(Conflict) 해결

### 충돌이 발생하는 상황

같은 파일의 같은 줄을 두 사람이 다르게 수정하고 merge할 때 발생

### 충돌 확인

```bash
git status
# both modified: src/login.js  ← 충돌 파일 표시
```

### 충돌 파일 내용

```
<<<<<<< HEAD (현재 내 브랜치 코드)
function login() {
  return "내가 수정한 코드";
}
======= (구분선)
function login() {
  return "다른 팀원이 수정한 코드";
}
>>>>>>> feature/other-branch (병합하려는 브랜치)
```

### 충돌 해결 순서

```bash
# 1. 충돌 파일 열어서 직접 수정
#    <<<<<<, =======, >>>>>>> 마커를 지우고 원하는 코드만 남김

# 2. 해결 완료 후 스테이징
git add src/login.js

# 3. 커밋
git commit -m "fix: 로그인 함수 충돌 해결"
```

### 충돌 예방법

```bash
# 작업 전 항상 최신화
git pull origin main

# 작업 중에도 주기적으로 main 변경사항 반영
git fetch origin
git rebase origin/main
```

---

## 자주 사용하는 명령어 총정리

### 📌 기본 상태 확인

```bash
git status                    # 변경 파일 확인
git log --oneline             # 커밋 히스토리 (한 줄)
git log --oneline --graph     # 브랜치 그래프 포함
git diff                      # 스테이징 전 변경사항 확인
git diff --staged             # 스테이징 후 변경사항 확인
```

### 📌 브랜치 관련

```bash
git branch                    # 로컬 브랜치 목록
git branch -r                 # 원격 브랜치 목록
git branch -a                 # 전체 브랜치 목록
git checkout -b 브랜치명      # 브랜치 생성 + 이동
git switch 브랜치명           # 브랜치 이동 (최신 방식)
git branch -d 브랜치명        # 로컬 브랜치 삭제 (안전)
git branch -D 브랜치명        # 로컬 브랜치 강제 삭제
```

### 📌 원격 저장소

```bash
git remote -v                         # 원격 저장소 목록 확인
git remote add origin URL             # 원격 저장소 추가
git remote add upstream URL           # 상위 저장소 추가 (fork용)
git fetch origin                      # 원격 변경사항 가져오기 (merge 안 함)
git pull origin main                  # 가져오기 + merge
git push origin 브랜치명              # 원격에 push
git push -u origin 브랜치명          # 업스트림 설정 후 push
git push origin --delete 브랜치명    # 원격 브랜치 삭제
```

### 📌 되돌리기

```bash
# 스테이징 취소 (파일 내용 유지)
git restore --staged 파일명

# 작업 파일 변경사항 취소 (⚠️ 복구 불가)
git restore 파일명

# 마지막 커밋 메시지 수정 (push 전에만!)
git commit --amend -m "새 메시지"

# 특정 커밋으로 되돌리기 (이력 보존)
git revert 커밋해시

# 특정 커밋으로 강제 이동 (⚠️ 협업 시 절대 금지)
git reset --hard 커밋해시
```

### 📌 stash (임시 저장)

```bash
# 작업 중 다른 브랜치로 이동해야 할 때 임시 저장
git stash

# stash 목록 확인
git stash list

# stash 복원
git stash pop

# stash 삭제
git stash drop
```

### 📌 merge vs rebase

```bash
# merge: 두 브랜치를 합치는 커밋 생성 (이력 보존)
git merge feature/브랜치명

# rebase: 커밋을 현재 브랜치 위에 재배치 (깔끔한 이력)
git rebase main

# ⚠️ rebase는 공유 브랜치(main)에서 사용 금지!
```

### 📌 태그

```bash
git tag v1.0.0                        # 태그 생성
git tag -a v1.0.0 -m "버전 1.0.0"    # 주석 있는 태그
git push origin v1.0.0               # 태그 push
git push origin --tags               # 모든 태그 push
```

---

## 주의사항 & 협업 에티켓

### 🚨 절대 하면 안 되는 것

```bash
# ❌ main(또는 develop)에 직접 push
git push origin main

# ❌ force push (협업 브랜치에서)
git push --force origin main

# ❌ 공유 브랜치에서 rebase
git rebase (main 브랜치에서)

# ❌ 민감한 정보 커밋 (비밀번호, API키 등)
git add .env  # .env는 반드시 .gitignore에!
```

### ✅ 반드시 지켜야 할 것

1. **작업 전 항상 `git pull`** — 최신 상태에서 시작
2. **기능별로 브랜치 분리** — 하나의 브랜치에 여러 기능 섞지 않기
3. **작은 단위로 자주 커밋** — 나중에 되돌리기 쉽고 리뷰도 쉬움
4. **의미있는 커밋 메시지** — 미래의 나와 팀원을 위해
5. **PR은 작게** — 500줄 이하가 리뷰하기 좋음
6. **.gitignore 설정** — 불필요한 파일 제외

### .gitignore 기본 예시

```gitignore
# 환경변수 (절대 커밋 금지!)
.env
.env.local

# 의존성 폴더
node_modules/
venv/
__pycache__/

# 빌드 결과물
dist/
build/
*.pyc

# IDE 설정
.vscode/
.idea/
*.swp

# OS 파일
.DS_Store
Thumbs.db

# 로그
*.log
```

---

## 긴급 상황 대처법

### 실수로 main에 push 했을 때

```bash
# 1. 되돌릴 커밋 확인
git log --oneline

# 2. 이전 커밋으로 revert (안전한 방법)
git revert HEAD
git push origin main

# 팀장/관리자에게 즉시 알리기!
```

### 잘못된 파일을 커밋했을 때 (push 전)

```bash
# 마지막 커밋 취소 (파일 변경사항은 유지)
git reset --soft HEAD~1

# 파일을 스테이징에서 제거
git restore --staged 잘못된파일.txt

# 다시 커밋
git commit -m "올바른 커밋 메시지"
```

### API 키를 실수로 커밋 & push 했을 때

```bash
# 즉시 해당 API 키 무효화! (GitHub이 이미 스캔했을 수 있음)
# 1. 해당 서비스에서 API 키 재발급
# 2. .gitignore에 파일 추가
# 3. git history에서 제거 (BFG Repo Cleaner 사용)
```

### 브랜치를 잘못 merge 했을 때

```bash
# merge 취소 (충돌 중일 때)
git merge --abort

# merge 커밋 되돌리기 (push 전)
git reset --hard HEAD~1
```

---

## 📊 협업 한눈에 보기

```
나의 로컬                GitHub 원격 저장소
─────────────           ──────────────────────
                         main (보호된 브랜치)
git checkout -b ──────▶ feature/내기능 (생성)
    [개발]
git add & commit
git push ─────────────▶ feature/내기능 (업데이트)
                         [PR 생성]
                         [코드 리뷰]
                         [Merge into main]
git checkout main
git pull ◀────────────── main (최신)
git branch -d ──────── [로컬 브랜치 삭제]
```

---

## 🔗 참고 자료

- [Git 공식 문서](https://git-scm.com/doc)
- [GitHub Docs](https://docs.github.com)
- [Conventional Commits](https://www.conventionalcommits.org/ko/)
- [GitHub Flow 가이드](https://docs.github.com/ko/get-started/quickstart/github-flow)

---

*작성일: 2026년 2월 | Git 협업 가이드 v1.0*
