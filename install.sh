# ⚙️ 원클릭 설치 — 논문 리뷰어 + 영업 시뮬레이터

## 실행 방법
```bash
chmod +x ~/free-services/install.sh
cd ~/free-services
./install.sh
```

## install.sh
```bash
#!/bin/bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🚀 AI 논문 리뷰어 + 영업 시뮬레이터 설치"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. agency-agents 업데이트
echo "[1/3] agency-agents 최신화..."
if [ -d ~/agency-agents ]; then
    cd ~/agency-agents && git pull --quiet
else
    git clone https://github.com/msitarzewski/agency-agents.git ~/agency-agents
fi

# 2. 논문 리뷰어 에이전트 복사
echo "[2/3] 논문 리뷰어 에이전트 설치..."
mkdir -p ~/.claude/agents
cp ~/agency-agents/academic/academic-narratologist.md ~/.claude/agents/
cp ~/agency-agents/academic/academic-psychologist.md ~/.claude/agents/
cp ~/agency-agents/academic/academic-anthropologist.md ~/.claude/agents/
cp ~/agency-agents/specialized/specialized-model-qa.md ~/.claude/agents/
cp ~/agency-agents/specialized/language-translator.md ~/.claude/agents/
cp ~/agency-agents/specialized/specialized-document-generator.md ~/.claude/agents/

# 3. 영업 시뮬레이터 에이전트 복사
echo "[2/3] 영업 시뮬레이터 에이전트 설치..."
cp ~/agency-agents/sales/sales-discovery-coach.md ~/.claude/agents/
cp ~/agency-agents/sales/sales-deal-strategist.md ~/.claude/agents/
cp ~/agency-agents/sales/sales-coach.md ~/.claude/agents/
cp ~/agency-agents/product/product-behavioral-nudge-engine.md ~/.claude/agents/
cp ~/agency-agents/sales/sales-pipeline-analyst.md ~/.claude/agents/
cp ~/agency-agents/specialized/organizational-psychologist.md ~/.claude/agents/
cp ~/agency-agents/specialized/specialized-strategy-duel-agent.md ~/.claude/agents/
cp ~/agency-agents/specialized/specialized-document-generator.md ~/.claude/agents/

echo "[3/3] 완료!"
echo ""
echo "✅ 설치 완료!"
echo ""
echo "📂 구조:"
echo "  ~/free-services/"
echo "  ├── paper-reviewer/README.md"
echo "  ├── sales-simulator/README.md"
echo "  ├── marketing/          (고객 유치 전략)"
echo "  └── install.sh"
echo ""
echo "🚀 사용법:"
echo "  claude (실행)"
echo "  → 논문 리뷰: @narratologist 이 논문 분석해줘 + 파일첨부"
echo "  → 영업 시뮬: @discovery-coach @deal-strategist 시뮬레이션 시작"
echo ""
echo "💰 완전 무료. Claude Pro $20/월만 있으면 끝."
```