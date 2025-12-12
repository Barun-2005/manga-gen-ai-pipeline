#!/bin/bash
# Git History Repair Script
# Created: 2025-12-12
# Purpose: Document steps used to clean large files from git history

# ============================================================================
# STEP 1: Backup current state
# ============================================================================
echo "Creating backup branch..."
git branch backup-before-cleanup

# ============================================================================
# STEP 2: Move large files to archive (already done in PowerShell)
# ============================================================================
# PowerShell commands used:
# Move-Item -Path "contest_package" -Destination "archive\legacy\contest_package" -Force
# Move-Item -Path "pipeline_v2" -Destination "archive\legacy\pipeline_v2" -Force
# + various phase scripts and test files

# ============================================================================
# STEP 3: Update .gitignore (already done)
# ============================================================================
# Added patterns for:
# *.safetensors, *.ckpt, *.pth, *.pt, *.bin, *.onnx
# artifacts/, ComfyUI-master/models/, archive/models/*

# ============================================================================
# STEP 4: Remove cached files (if any were tracked)
# ============================================================================
# Check if any large files are still tracked:
# git ls-files "*.safetensors" "*.ckpt" "*.pth" "*.pt" "*.bin"

# If files are found, remove from git cache (not disk):
# git rm --cached "*.safetensors"
# git rm --cached "*.ckpt"
# git rm --cached ComfyUI-master/models/ -r

# ============================================================================
# STEP 5: If files exist in history, use BFG Repo-Cleaner
# ============================================================================
# Download BFG: https://rtyley.github.io/bfg-repo-cleaner/
#
# WARNING: This rewrites git history. Coordinate with team before running.
#
# Commands to run:
# java -jar bfg.jar --strip-blobs-bigger-than 100M .
# java -jar bfg.jar --delete-files "*.safetensors" .
# git reflog expire --expire=now --all && git gc --prune=now --aggressive
#
# After cleanup:
# git push origin --force --all
# git push origin --force --tags

# ============================================================================
# STEP 6: Verify cleanup
# ============================================================================
# Check repository size:
# du -sh .git
# git count-objects -vH

# ============================================================================
# REVERT INSTRUCTIONS
# ============================================================================
# If something goes wrong:
# git checkout backup-before-cleanup
# git branch -D master
# git branch -m master
