#!/bin/bash
# push-to-github.sh — 上传 teonu-worldmodel 到 GitHub
set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

REPO_NAME="teonu-worldmodel"
GITHUB_USER="${GITHUB_USER:-billgaohub}"

echo "=== 上传 $REPO_NAME 到 GitHub ==="

# 检查远程是否已配置
if ! git remote -v | grep -q origin; then
    echo "⚠️  未检测到 git remote，正在创建 GitHub 仓库并配置..."

    # 创建 GitHub 仓库（需要 gh CLI）
    gh repo create "$REPO_NAME" --public --source=. --push || true
else
    echo "✓ Git remote 已配置: $(git remote get-url origin)"
    echo "请手动 push 或修改 remote 后执行: git push -u origin main"
fi

echo "=== 完成 ==="
