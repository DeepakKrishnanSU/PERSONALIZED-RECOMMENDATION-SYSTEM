/**
 * NexusAI Master Application Client Script (app.js)
 * Experiment 4: Building Applications using GPT-4 (24CS2506)
 *
 * Implements end-to-end frontend interactivity:
 * - Profile validation, synthesis, and prompt construction (Q1-Q4)
 * - LLM recommendation execution and suitability leaderboard (Q5-Q6)
 * - Deep pedagogical explanations in modal dialog (Q7)
 * - Natural language continuous feedback & refinement (Q8)
 * - Autonomous cognitive intent detection console (Q9)
 * - Session persistence to outputs/recommendations.txt & file inspector (Q10)
 */

'use strict';

document.addEventListener('DOMContentLoaded', () => {
  // ========================================================
  // 1. STATE & UTILITIES
  // ========================================================
  const state = {
    profile: null,
    preferences: null,
    prompt: null,
    recommendations: [],
    refinedRecommendations: [],
    isGenerating: false,
    isRefining: false
  };

  const $ = (selector, context = document) => context.querySelector(selector);
  const $$ = (selector, context = document) => [...context.querySelectorAll(selector)];

  const refreshIcons = () => {
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
  };

  const escapeHtml = (str) => {
    if (typeof str !== 'string') return String(str || '');
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  };

  // Toast Notification System
  const showToast = (message, type = 'info', duration = 3800) => {
    const container = $('#toastContainer') || (() => {
      const el = document.createElement('div');
      el.id = 'toastContainer';
      el.className = 'toast-container';
      el.setAttribute('aria-live', 'polite');
      document.body.appendChild(el);
      return el;
    })();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const iconMap = {
      success: 'check-circle',
      error: 'alert-circle',
      info: 'info'
    };
    const iconName = iconMap[type] || 'info';

    toast.innerHTML = `
      <i data-lucide="${iconName}"></i>
      <span>${escapeHtml(message)}</span>
    `;

    container.appendChild(toast);
    refreshIcons();

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(12px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 320);
    }, duration);
  };

  // Generic Modal Controller
  const openModal = (modalEl) => {
    if (!modalEl) return;
    modalEl.style.display = 'flex';
    modalEl.setAttribute('aria-hidden', 'false');
    refreshIcons();
  };

  const closeModal = (modalEl) => {
    if (!modalEl) return;
    modalEl.style.display = 'none';
    modalEl.setAttribute('aria-hidden', 'true');
  };

  // ========================================================
  // 2. MODALS & SYSTEM ARCHITECTURE
  // ========================================================
  const archModal = $('#architectureModal');
  const btnOpenArch = $('#btnOpenArchModal');
  const btnCloseArch = $('#btnCloseArchModal');
  const btnDismissArch = $('#btnDismissArchModal');

  btnOpenArch?.addEventListener('click', () => openModal(archModal));
  btnCloseArch?.addEventListener('click', () => closeModal(archModal));
  btnDismissArch?.addEventListener('click', () => closeModal(archModal));

  const explanationModal = $('#explanationModal');
  const btnCloseModal = $('#btnCloseModal');
  const btnDismissModal = $('#btnDismissModal');
  btnCloseModal?.addEventListener('click', () => closeModal(explanationModal));
  btnDismissModal?.addEventListener('click', () => closeModal(explanationModal));

  const fileInspectorModal = $('#fileInspectorModal');
  const btnCloseFileModal = $('#btnCloseFileModal');
  const btnDismissFileModal = $('#btnDismissFileModal');
  btnCloseFileModal?.addEventListener('click', () => closeModal(fileInspectorModal));
  btnDismissFileModal?.addEventListener('click', () => closeModal(fileInspectorModal));

  // Close modals on overlay backdrop click
  [archModal, explanationModal, fileInspectorModal].forEach(modal => {
    modal?.addEventListener('mousedown', (e) => {
      if (e.target === modal) closeModal(modal);
    });
  });

  // ========================================================
  // 3. TABS SWITCHER (Active Profile / Analysis / Prompt)
  // ========================================================
  const tabButtons = $$('.tab-switcher .tab-btn');
  const tabPanels = $$('.tab-body-container .tab-panel');

  const switchTab = (targetTabId) => {
    tabButtons.forEach(btn => {
      const isActive = btn.dataset.tab === targetTabId || btn.id === targetTabId;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    tabPanels.forEach(panel => {
      const match = panel.id === targetTabId;
      panel.classList.toggle('active', match);
    });
    refreshIcons();
  };

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.dataset.tab;
      if (targetId) switchTab(targetId);
    });
  });

  // Copy Prompt Button
  const btnCopyPrompt = $('#btnCopyPrompt');
  btnCopyPrompt?.addEventListener('click', async () => {
    const code = $('#displayPromptCode')?.textContent || '';
    if (!code) {
      showToast('Prompt is empty.', 'error');
      return;
    }
    try {
      await navigator.clipboard.writeText(code);
      showToast('Prompt copied to clipboard!', 'success');
      const copySpan = btnCopyPrompt.querySelector('span');
      if (copySpan) {
        const originalText = copySpan.textContent;
        copySpan.textContent = 'Copied!';
        setTimeout(() => { copySpan.textContent = originalText; }, 2000);
      }
    } catch {
      showToast('Could not copy prompt automatically.', 'error');
    }
  });

  // ========================================================
  // 4. PROFILE FORM & SYNTHESIS (Q1, Q2, Q3)
  // ========================================================
  const profileForm = $('#profileForm');
  const inputName = $('#inputName');
  const inputAge = $('#inputAge');
  const inputBackground = $('#inputBackground');
  const inputInterests = $('#inputInterests');
  const selectSkillLevel = $('#selectSkillLevel');
  const selectCategory = $('#selectCategory');
  const inputGoal = $('#inputGoal');
  const inputCount = $('#inputCount');

  // Interactive Interest Chip Tags
  $$('.tag-chips-wrapper .chip-tag').forEach(tag => {
    tag.addEventListener('click', () => {
      const val = tag.dataset.interest;
      if (!val || !inputInterests) return;
      const currentList = inputInterests.value
        .split(',')
        .map(s => s.trim())
        .filter(Boolean);

      if (!currentList.includes(val)) {
        currentList.push(val);
        inputInterests.value = currentList.join(', ');
        showToast(`Added interest: "${val}"`, 'info');
      } else {
        inputInterests.value = currentList.filter(i => i !== val).join(', ');
        showToast(`Removed interest: "${val}"`, 'info');
      }
    });
  });

  // Updates Right Preview Card with synthesized Profile data
  const updateProfileUI = (profile, preferences, prompt) => {
    if (!profile) return;

    // Tab 1: Profile View
    const avatarEl = $('#profileAvatarInitial');
    if (avatarEl) avatarEl.textContent = (profile.name || 'U').charAt(0).toUpperCase();

    const nameEl = $('#displayProfileName');
    if (nameEl) nameEl.textContent = profile.name || '--';

    const bgEl = $('#displayProfileBackground');
    if (bgEl) bgEl.textContent = profile.background || '--';

    const lvlEl = $('#displayProfileLevel');
    if (lvlEl) lvlEl.textContent = profile.skill_level || '--';

    const ageEl = $('#displayProfileAge');
    if (ageEl) ageEl.textContent = `${profile.age || 20} Years`;

    const interestsEl = $('#displayProfileInterests');
    if (interestsEl) {
      interestsEl.textContent = Array.isArray(profile.interests)
        ? profile.interests.join(', ')
        : (profile.interests || '--');
    }

    const prefEl = $('#displayProfilePreference');
    if (prefEl) prefEl.textContent = profile.preferred_category || '--';

    const goalEl = $('#displayProfileGoal');
    if (goalEl) goalEl.textContent = profile.goal || '--';

    const countEl = $('#displayProfileCount');
    if (countEl) countEl.textContent = `${profile.num_recommendations || 5} Recommendations`;

    // Tab 2: Preferences Analysis
    if (preferences) {
      const primEl = $('#displayPrimaryInterest');
      if (primEl) primEl.textContent = preferences.primary_interest || profile.interests?.[0] || 'AI';

      const secEl = $('#displaySecondaryInterest');
      if (secEl) secEl.textContent = preferences.secondary_interest || profile.interests?.[1] || 'Python';

      const skillTag = $('#displaySkillTag');
      if (skillTag) skillTag.textContent = preferences.skill_level || profile.skill_level;

      const formatTag = $('#displayFormatTag');
      if (formatTag) formatTag.textContent = preferences.preferred_format || profile.preferred_category;

      const goalTag = $('#displayGoalTag');
      if (goalTag) goalTag.textContent = preferences.target_goal || profile.goal;

      const constrEl = $('#displayConstraintsText');
      if (constrEl && preferences.pedagogical_constraints) {
        constrEl.textContent = preferences.pedagogical_constraints;
      }
    }

    // Tab 3: Formulated Prompt
    if (prompt) {
      const promptCode = $('#displayPromptCode');
      if (promptCode) promptCode.textContent = prompt;
    }

    refreshIcons();
  };

  // Submit Profile Form
  const submitProfileForm = async () => {
    const payload = {
      name: inputName?.value.trim() || 'Arun',
      age: parseInt(inputAge?.value || '20', 10),
      background: inputBackground?.value.trim() || 'Computer Science',
      interests: inputInterests?.value.trim() || 'Artificial Intelligence, Python',
      skill_level: selectSkillLevel?.value || 'Beginner',
      preferred_category: selectCategory?.value || 'Practical learning',
      goal: inputGoal?.value.trim() || 'Learn AI',
      num_recommendations: parseInt(inputCount?.value || '5', 10)
    };

    const submitBtn = $('#btnSynthesizeProfile');
    const originalText = submitBtn?.innerHTML;
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="btn-spinner"></span> <span>Synthesizing Profile...</span>';
    }

    try {
      const res = await fetch('/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (!res.ok || data.status !== 'success') {
        throw new Error(data.message || 'Profile synthesis failed.');
      }

      state.profile = data.profile;
      state.preferences = data.preferences;
      state.prompt = data.prompt;

      updateProfileUI(state.profile, state.preferences, state.prompt);
      showToast(`Profile for ${data.profile.name} synthesized successfully!`, 'success');

      // Auto-switch to Cognitive Analysis tab for a brief moment then back to Profile
      switchTab('tabContentProfile');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
        refreshIcons();
      }
    }
  };

  profileForm?.addEventListener('submit', (e) => {
    e.preventDefault();
    submitProfileForm();
  });

  // Demo Profile Navbar Quick Load
  const btnQuickSample = $('#btnQuickSample');
  btnQuickSample?.addEventListener('click', () => {
    if (inputName) inputName.value = 'Arun';
    if (inputAge) inputAge.value = '20';
    if (inputBackground) inputBackground.value = 'Computer Science';
    if (inputInterests) inputInterests.value = 'Artificial Intelligence, Python';
    if (selectSkillLevel) selectSkillLevel.value = 'Beginner';
    if (selectCategory) selectCategory.value = 'Practical learning';
    if (inputGoal) inputGoal.value = 'Learn AI';
    if (inputCount) inputCount.value = '5';

    showToast('Loaded standard Lab Profile ("Arun"). Analyzing...', 'info');
    submitProfileForm();
    const studio = $('#studioSection');
    studio?.scrollIntoView({ behavior: 'smooth' });
  });

  // ========================================================
  // 5. RECOMMENDATIONS & LEADERBOARD (Q4, Q5, Q6)
  // ========================================================
  const btnGenerate = $('#btnGenerateRecommendations');
  const genSpinner = $('#genSpinner');
  const recommendationsList = $('#recommendationsList');
  const emptyStatePlaceholder = $('#emptyStatePlaceholder');
  const tabularRankingCard = $('#tabularRankingCard');
  const rankingTableBody = $('#rankingTableBody');
  const valTotalItems = $('#valTotalItems');
  const valTopScore = $('#valTopScore');

  // Render individual card
  const createRecCard = (item, rank) => {
    const card = document.createElement('div');
    card.className = `recommendation-card rec-rank-${rank <= 3 ? rank : 'other'}`;
    const scoreVal = typeof item.score === 'number' ? item.score : parseInt(item.score, 10) || 85;

    card.innerHTML = `
      <div class="rec-rank-box">
        <span class="rec-rank-label">Rank</span>
        <span class="rec-rank-num">#${rank}</span>
      </div>
      <div class="rec-content-box">
        <h3 class="rec-title">${escapeHtml(item.name || 'Learning Resource')}</h3>
        <p class="rec-reason">${escapeHtml(item.reason || item.explanation || 'Matches active profile vector.')}</p>
      </div>
      <div class="rec-action-box">
        <div class="rec-score-chip">
          <i data-lucide="award"></i>
          <span>${scoreVal}%</span>
        </div>
        <button class="btn-explain" data-name="${escapeHtml(item.name)}" data-reason="${escapeHtml(item.reason || '')}" data-score="${scoreVal}">
          <i data-lucide="help-circle"></i>
          <span>Why this?</span>
        </button>
      </div>
    `;

    const explainBtn = card.querySelector('.btn-explain');
    explainBtn?.addEventListener('click', () => {
      handleExplainItem(item.name, item.reason || '', scoreVal);
    });

    return card;
  };

  // Render Leaderboard Table
  const renderTableRows = (items) => {
    if (!rankingTableBody) return;
    rankingTableBody.innerHTML = '';

    items.forEach((item, idx) => {
      const rank = idx + 1;
      const scoreVal = typeof item.score === 'number' ? item.score : parseInt(item.score, 10) || 85;
      const statusText = scoreVal >= 90 ? 'High Fit' : (scoreVal >= 80 ? 'Optimal' : 'Moderate');

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="td-rank">#${rank}</td>
        <td class="td-name"><strong>${escapeHtml(item.name)}</strong></td>
        <td class="td-score">${scoreVal}%</td>
        <td class="td-status"><span class="badge-alignment">${statusText}</span></td>
      `;
      rankingTableBody.appendChild(tr);
    });
  };

  // Trigger Generation
  const executeGeneration = async () => {
    if (state.isGenerating) return;

    if (!state.profile) {
      // Auto-synthesize profile first if user hasn't pressed the button yet
      await submitProfileForm();
      if (!state.profile) return;
    }

    state.isGenerating = true;
    if (btnGenerate) {
      btnGenerate.disabled = true;
      if (genSpinner) genSpinner.style.display = 'inline-block';
      const label = btnGenerate.querySelector('span');
      if (label) label.textContent = 'Generating via Cognitive LLM Core...';
    }

    const startTime = performance.now();
    showToast('Invoking LLM for personalized synthesis and rankings...', 'info');

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await res.json();

      if (!res.ok || data.status !== 'success') {
        throw new Error(data.message || 'Generation failed.');
      }

      state.recommendations = data.recommendations || [];
      const latencySec = ((performance.now() - startTime) / 1000).toFixed(2);

      // Update Meta Strip
      if (valTotalItems) valTotalItems.textContent = `${state.recommendations.length} Items`;
      if (valTopScore && state.recommendations.length > 0) {
        valTopScore.textContent = `${state.recommendations[0].score}%`;
      }

      // Hide empty state and populate stream
      if (emptyStatePlaceholder) emptyStatePlaceholder.style.display = 'none';
      if (recommendationsList) {
        recommendationsList.innerHTML = '';
        state.recommendations.forEach((item, index) => {
          recommendationsList.appendChild(createRecCard(item, index + 1));
        });
      }

      // Populate Table
      renderTableRows(state.recommendations);
      if (tabularRankingCard) tabularRankingCard.style.display = 'block';

      showToast(`Synthesized ${state.recommendations.length} recommendations in ${latencySec}s!`, 'success');

      // Smooth scroll to results
      const rankings = $('#rankingsSection');
      rankings?.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      state.isGenerating = false;
      if (btnGenerate) {
        btnGenerate.disabled = false;
        if (genSpinner) genSpinner.style.display = 'none';
        const label = btnGenerate.querySelector('span');
        if (label) label.textContent = 'Execute Neural Generation & Ranking';
      }
      refreshIcons();
    }
  };

  btnGenerate?.addEventListener('click', executeGeneration);

  // ========================================================
  // 6. EXPLANATION MODAL (Q7)
  // ========================================================
  const modalItemTitle = $('#modalItemTitle');
  const modalItemScore = $('#modalItemScore');
  const modalExplanationContent = $('#modalExplanationContent');

  const handleExplainItem = async (itemName, reason, score) => {
    if (!state.profile) {
      showToast('Profile required to construct personalized rationale.', 'error');
      return;
    }

    if (modalItemTitle) modalItemTitle.textContent = itemName;
    if (modalItemScore) modalItemScore.textContent = `Suitability Score: ${score}%`;
    if (modalExplanationContent) {
      modalExplanationContent.innerHTML = `
        <div style="display:flex; align-items:center; gap:0.75rem; color:#818cf8; padding: 1rem 0;">
          <span class="btn-spinner"></span>
          <span>Consulting GPT-4 reasoning engine for deep explanation...</span>
        </div>
      `;
    }

    openModal(explanationModal);

    try {
      const res = await fetch('/api/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_name: itemName, reason: reason })
      });
      const data = await res.json();

      if (!res.ok || data.status !== 'success') {
        throw new Error(data.message || 'Explanation failed.');
      }

      if (modalExplanationContent) {
        modalExplanationContent.innerHTML = `
          <div class="explanation-rich-text">
            <p style="font-size: 1.05rem; line-height: 1.7; color: #e2e8f0; margin-bottom: 1rem;">
              ${escapeHtml(data.explanation || reason)}
            </p>
            <div style="margin-top: 1.25rem; padding: 0.85rem 1rem; border-radius: var(--radius-sm); background: rgba(99, 102, 241, 0.08); border: 1px solid rgba(99, 102, 241, 0.2); font-size: 0.8125rem; color: #94a3b8;">
              <strong style="color: #c7d2fe;">Pedagogical Context:</strong> Tailored specifically for <em>${escapeHtml(state.profile.name)}</em> (${escapeHtml(state.profile.skill_level)} in ${escapeHtml(state.profile.background)} aiming to ${escapeHtml(state.profile.goal)}).
            </div>
          </div>
        `;
      }
    } catch (err) {
      if (modalExplanationContent) {
        modalExplanationContent.innerHTML = `<span style="color: #f43f5e;">Error: ${escapeHtml(err.message)}</span>`;
      }
    }
  };

  // ========================================================
  // 7. USER FEEDBACK & REFINEMENT (Q8)
  // ========================================================
  const inputUserFeedback = $('#inputUserFeedback');
  const btnClearFeedback = $('#btnClearFeedback');
  const btnSubmitFeedback = $('#btnSubmitFeedback');
  const refinedResultsDrawer = $('#refinedResultsDrawer');
  const appliedFeedbackPill = $('#appliedFeedbackPill');
  const refinedItemsGrid = $('#refinedItemsGrid');

  // Quick Adjustment Preset Pills
  $$('.feedback-quick-pills .quick-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      const fb = pill.dataset.feedback;
      if (fb && inputUserFeedback) {
        inputUserFeedback.value = fb;
        inputUserFeedback.focus();
        showToast('Feedback template applied. Click Submit to refine!', 'info');
      }
    });
  });

  btnClearFeedback?.addEventListener('click', () => {
    if (inputUserFeedback) inputUserFeedback.value = '';
  });

  const submitFeedback = async () => {
    const feedbackText = inputUserFeedback?.value.trim();
    if (!feedbackText) {
      showToast('Please type your feedback or pick a quick adjustment above.', 'error');
      inputUserFeedback?.focus();
      return;
    }

    if (!state.profile || state.recommendations.length === 0) {
      showToast('Generate recommendations first before refining.', 'error');
      return;
    }

    state.isRefining = true;
    if (btnSubmitFeedback) {
      btnSubmitFeedback.disabled = true;
      btnSubmitFeedback.innerHTML = '<span class="btn-spinner"></span> <span>Refining Recommendations...</span>';
    }

    try {
      const res = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feedback: feedbackText })
      });
      const data = await res.json();

      if (!res.ok || data.status !== 'success') {
        throw new Error(data.message || 'Feedback refinement failed.');
      }

      state.refinedRecommendations = data.refined_recommendations || [];

      if (appliedFeedbackPill) {
        appliedFeedbackPill.textContent = `Critique: "${feedbackText.substring(0, 50)}${feedbackText.length > 50 ? '...' : ''}"`;
      }

      if (refinedItemsGrid) {
        refinedItemsGrid.innerHTML = '';
        state.refinedRecommendations.forEach((item, index) => {
          refinedItemsGrid.appendChild(createRecCard(item, index + 1));
        });
      }

      if (refinedResultsDrawer) refinedResultsDrawer.style.display = 'block';

      showToast(`Refined recommendations updated (${state.refinedRecommendations.length} items)!`, 'success');
      refinedResultsDrawer?.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      state.isRefining = false;
      if (btnSubmitFeedback) {
        btnSubmitFeedback.disabled = false;
        btnSubmitFeedback.innerHTML = '<i data-lucide="refresh-cw"></i> <span>Submit Feedback & Refine</span>';
      }
      refreshIcons();
    }
  };

  btnSubmitFeedback?.addEventListener('click', submitFeedback);

  // ========================================================
  // 8. INTELLIGENT INTENT DETECTION CONSOLE (Q9)
  // ========================================================
  const inputIntentQuery = $('#inputIntentQuery');
  const btnDetectIntent = $('#btnDetectIntent');
  const intentResultCard = $('#intentResultCard');
  const valDetectedIntent = $('#valDetectedIntent');
  const valIntentRationale = $('#valIntentRationale');

  // Sample Intent Chips
  $$('.intent-sample-chips .intent-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const query = chip.dataset.query;
      if (query && inputIntentQuery) {
        inputIntentQuery.value = query;
        detectIntentQuery();
      }
    });
  });

  const detectIntentQuery = async () => {
    const query = inputIntentQuery?.value.trim();
    if (!query) {
      showToast('Enter a natural language command to decode.', 'error');
      inputIntentQuery?.focus();
      return;
    }

    if (btnDetectIntent) {
      btnDetectIntent.disabled = true;
      btnDetectIntent.innerHTML = '<span class="btn-spinner"></span> <span>Decoding...</span>';
    }

    try {
      const res = await fetch('/api/intent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await res.json();

      if (!res.ok || data.status !== 'success') {
        throw new Error(data.message || 'Intent detection failed.');
      }

      if (valDetectedIntent) valDetectedIntent.textContent = data.intent;
      if (valIntentRationale) valIntentRationale.textContent = data.reason;
      if (intentResultCard) intentResultCard.style.display = 'block';

      showToast(`Decoded Intent: ${data.intent}`, 'info');

      // Autonomous reactive trigger based on detected intent
      handleAutonomousAction(data.intent, query);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      if (btnDetectIntent) {
        btnDetectIntent.disabled = false;
        btnDetectIntent.innerHTML = '<i data-lucide="cpu"></i> <span>Decode Intent</span>';
      }
      refreshIcons();
    }
  };

  // Autonomous action dispatcher for Q9 / Q10
  const handleAutonomousAction = (intent, query) => {
    switch (intent) {
      case 'GENERATE_RECOMMENDATION':
        executeGeneration();
        break;

      case 'REFINE_RECOMMENDATION':
        if (inputUserFeedback) {
          inputUserFeedback.value = query;
          inputUserFeedback.scrollIntoView({ behavior: 'smooth' });
          inputUserFeedback.focus();
        }
        break;

      case 'SHOW_PROFILE':
        switchTab('tabContentProfile');
        $('#studioSection')?.scrollIntoView({ behavior: 'smooth' });
        break;

      case 'EXPLAIN_RECOMMENDATION':
        if (state.recommendations.length > 0) {
          const first = state.recommendations[0];
          handleExplainItem(first.name, first.reason || '', first.score || 95);
        } else {
          showToast('Generate recommendations first to inspect explanations.', 'info');
        }
        break;

      case 'SAVE_RECOMMENDATION':
        saveSessionToFile();
        break;

      case 'EXIT':
        showToast('Exit command acknowledged. Session state preserved.', 'info');
        break;

      default:
        break;
    }
  };

  btnDetectIntent?.addEventListener('click', detectIntentQuery);
  inputIntentQuery?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      detectIntentQuery();
    }
  });

  // ========================================================
  // 9. PERSISTENCE & FILE VAULT (Q10)
  // ========================================================
  const btnSaveToFile = $('#btnSaveToFile');
  const saveConfirmationCard = $('#saveConfirmationCard');
  const valSaveMessage = $('#valSaveMessage');
  const valSavePath = $('#valSavePath');
  const valSaveTimestamp = $('#valSaveTimestamp');
  const btnViewSavedFile = $('#btnViewSavedFile');
  const filePreviewContent = $('#filePreviewContent');
  const btnExportSession = $('#btnExportSession');

  const saveSessionToFile = async () => {
    if (!state.profile || state.recommendations.length === 0) {
      showToast('Generate recommendations before saving output.', 'error');
      return;
    }

    if (btnSaveToFile) {
      btnSaveToFile.disabled = true;
      btnSaveToFile.innerHTML = '<span class="btn-spinner"></span> <span>Writing Report...</span>';
    }

    try {
      const res = await fetch('/api/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await res.json();

      if (!res.ok || data.status !== 'success') {
        throw new Error(data.message || 'Saving failed.');
      }

      if (valSaveMessage) valSaveMessage.textContent = data.message || 'Recommendation Saved Successfully';
      if (valSavePath) valSavePath.textContent = `Path: ${data.file_path || 'outputs/recommendations.txt'}`;
      if (valSaveTimestamp) valSaveTimestamp.textContent = data.timestamp || new Date().toLocaleString();
      if (saveConfirmationCard) saveConfirmationCard.style.display = 'flex';

      showToast('Exported session report to outputs/recommendations.txt!', 'success');
      saveConfirmationCard?.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      if (btnSaveToFile) {
        btnSaveToFile.disabled = false;
        btnSaveToFile.innerHTML = '<i data-lucide="save"></i> <span>Save Recommendations to File</span>';
      }
      refreshIcons();
    }
  };

  btnSaveToFile?.addEventListener('click', saveSessionToFile);

  // Inspect Saved File in Modal
  btnViewSavedFile?.addEventListener('click', async () => {
    if (filePreviewContent) filePreviewContent.textContent = 'Reading outputs/recommendations.txt...';
    openModal(fileInspectorModal);

    try {
      const res = await fetch('/api/view-saved');
      const data = await res.json();
      if (!res.ok || data.status !== 'success') {
        throw new Error(data.message || 'Could not load file.');
      }
      if (filePreviewContent) filePreviewContent.textContent = data.content;
    } catch (err) {
      if (filePreviewContent) filePreviewContent.textContent = `Error reading file: ${err.message}`;
    }
  });

  // Export Session button in Navbar
  btnExportSession?.addEventListener('click', async () => {
    if (!state.profile || state.recommendations.length === 0) {
      showToast('No recommendations generated yet to export. Running demo profile...', 'info');
      await submitProfileForm();
      await executeGeneration();
    }
    // Direct browser download
    window.location.href = '/api/download-saved';
    showToast('Downloading recommendations.txt report...', 'success');
  });

  // Hero Quick Navigation Buttons
  $('#btnGetStarted')?.addEventListener('click', (e) => {
    e.preventDefault();
    $('#studioSection')?.scrollIntoView({ behavior: 'smooth' });
  });

  $('#btnExploreIntents')?.addEventListener('click', (e) => {
    e.preventDefault();
    $('#intentConsole')?.scrollIntoView({ behavior: 'smooth' });
    $('#inputIntentQuery')?.focus();
  });

  // ========================================================
  // 10. INITIALIZATION
  // ========================================================
  refreshIcons();
});
