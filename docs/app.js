/* PaperCash discovery: public metadata, local reading list, no account required. */
'use strict';

(() => {
  const $ = (selector) => document.querySelector(selector);
  const STORAGE_KEY = 'papercash.saved.v1';
  const SETUP_PROMPT = '帮我安装 https://github.com/Jesseovo/PaperCash ，按 SKILL.md 配置独立环境并验证可用，然后问我想研究什么。';
  const icons = {
    bookmark: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 4h12v17l-6-4-6 4z"/></svg>',
    copy: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 8h12v13H8zM4 16H2V2h13v2"/></svg>',
    arrow: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 18 18 6M6 6h12v12"/></svg>',
  };
  const state = { papers: [], topics: [], topic: 'all', source: 'all', query: '',
    sort: 'newest', savedOnly: false, visible: 12, saved: {}, ready: false, featured: null };
  let toastTimer;
  let activeCopy = '';

  function element(tag, className = '', text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function safeUrl(value) {
    try {
      const url = new URL(value);
      return url.protocol === 'https:' && !url.username && !url.password ? url.href : '';
    } catch { return ''; }
  }

  function validPaper(paper) {
    return paper && typeof paper.id === 'string' && typeof paper.title === 'string'
      && Array.isArray(paper.authors) && Array.isArray(paper.topics)
      && typeof paper.citations === 'object' && paper.citations !== null && safeUrl(paper.url);
  }

  function loadSaved() {
    try {
      const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
      if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
      return Object.fromEntries(Object.entries(value).filter(([id, paper]) => validPaper(paper) && id === paper.id));
    } catch { return {}; }
  }

  function toast(message) {
    clearTimeout(toastTimer);
    $('#toast').textContent = message;
    $('#toast').hidden = false;
    toastTimer = setTimeout(() => { $('#toast').hidden = true; }, 2800);
  }

  async function copyText(text, success) {
    try {
      await navigator.clipboard.writeText(text);
      toast(success || '已复制');
      return true;
    } catch {
      const field = $('#paper-dialog textarea');
      if (field) { field.focus(); field.select(); }
      toast('自动复制未成功，请在弹窗中选择文字并手动复制。');
      return false;
    }
  }

  function topicLabel(id) { return state.topics.find(t => t.id === id)?.label || id; }
  function authors(paper, limit = 3) {
    const names = paper.authors.slice(0, limit).join(', ');
    return names ? names + (paper.authors.length > limit ? ' et al.' : '') : '来源未提供作者信息';
  }
  function dateLabel(value) { return value || '日期未提供'; }
  function timestamp(value) {
    if (!value) return '尚无成功更新';
    const date = new Date(value);
    if (Number.isNaN(date.valueOf())) return '更新时间未知';
    return new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', year: 'numeric',
      month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).format(date);
  }

  function externalLink(label, url, className) {
    const a = element('a', className, label);
    a.href = safeUrl(url);
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    return a;
  }

  function toggleSaved(paper) {
    const next = { ...state.saved };
    const wasSaved = Boolean(next[paper.id]);
    if (wasSaved) delete next[paper.id];
    else next[paper.id] = paper;
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)); }
    catch { toast('书签未能保存，请检查浏览器存储是否可用。'); return; }
    state.saved = next;
    render();
    toast(wasSaved ? '已从书签移除' : '已放进你的书签，下次还在这里。');
  }

  function dialogBase(title, eyebrow = 'A LITTLE HELP') {
    const dialog = $('#paper-dialog');
    $('#dialog-title').textContent = title;
    $('#dialog-eyebrow').textContent = eyebrow;
    $('#dialog-body').replaceChildren();
    $('#dialog-actions').replaceChildren();
    if (!dialog.open) dialog.showModal();
    return { body: $('#dialog-body'), actions: $('#dialog-actions') };
  }

  function actionButton(label, onClick, primary = false) {
    const button = element('button', `button ${primary ? 'button-primary' : 'button-text'}`, label);
    button.type = 'button';
    button.addEventListener('click', onClick);
    return button;
  }

  function showPrompt(title, prompt, introduction) {
    const { body, actions } = dialogBase(title, 'KEEP THE CURIOSITY GOING');
    body.append(element('p', 'dialog-intro', introduction));
    const field = element('textarea', 'prompt-box');
    field.readOnly = true;
    field.value = prompt;
    field.setAttribute('aria-label', '可复制的 Agent 指令');
    body.append(field);
    actions.append(actionButton('复制指令，交给 Agent ↗', () => copyText(prompt, '已复制，把这句话发给你的 Agent 即可。'), true));
  }

  function setup() {
    showPrompt('一句话，研究就从这里开始。', SETUP_PROMPT,
      '发给能执行本地命令的 Agent，它会根据项目指南准备环境，再陪你开始研究。');
  }

  function research(paper) {
    const prompt = `${SETUP_PROMPT}\n\n我想进一步研究这篇论文：\n标题：${paper.title}\n作者：${authors(paper, 10)}\n来源：${paper.url}${paper.doi ? `\nDOI：${paper.doi}` : ''}\n\n请先核实论文元数据，整理可用摘要，检索相关研究并保留来源链接；如果没有读到全文，请明确说明，不要把摘要整理称为全文综述。最后给我一份阅读路径和待核实的问题。`;
    showPrompt('把这份好奇心，交给 Agent。', prompt,
      '这段指令带上了论文标题与来源。复制给你的 Agent，继续寻找相关研究。');
  }

  function citation(paper) {
    const { body, actions } = dialogBase(paper.title, 'A CITATION TO TAKE WITH YOU');
    const tabs = element('div', 'citation-tabs');
    tabs.setAttribute('role', 'group');
    tabs.setAttribute('aria-label', '引用格式');
    const output = element('pre', 'citation-output');
    output.setAttribute('aria-live', 'polite');
    const labels = { gb7714: 'GB/T 7714', apa: 'APA', bibtex: 'BibTeX' };
    for (const [style, label] of Object.entries(labels)) {
      const button = element('button', '', label);
      button.type = 'button';
      button.setAttribute('aria-pressed', style === 'gb7714' ? 'true' : 'false');
      button.addEventListener('click', () => {
        for (const b of tabs.children) b.setAttribute('aria-pressed', b === button ? 'true' : 'false');
        activeCopy = paper.citations[style] || '来源信息不足，暂不能生成此格式。';
        output.textContent = activeCopy;
      });
      tabs.append(button);
    }
    activeCopy = paper.citations.gb7714 || '';
    output.textContent = activeCopy;
    body.append(tabs, output, element('p', 'citation-note', '基于来源元数据生成的引用草稿，提交前请核对作者、日期与学校或期刊规范。'));
    actions.append(externalLink('查看来源 ↗', paper.url, 'button button-text'),
      actionButton('复制引用', async () => {
        if (!await copyText(activeCopy, '引用已复制。')) {
          showPrompt('手动复制引用', activeCopy, '浏览器未允许自动复制，请选择下方内容。');
          $('#paper-dialog textarea').select();
        }
      }, true));
  }

  function detail(paper) {
    const { body, actions } = dialogBase(paper.title, 'ONE PAPER, ONE NEW POSSIBILITY');
    body.append(element('p', 'dialog-meta', `${authors(paper, 10)}\n${dateLabel(paper.published)} · ${paper.venue || paper.source} · ${paper.kind === 'preprint' ? '预印本' : '出版文献'}`));
    body.append(element('div', 'dialog-abstract', paper.abstract || '来源没有提供摘要。你可以前往原文页面查看，或将这篇论文交给 Agent 继续检索。'));
    body.append(externalLink('打开论文原文页面 ↗', paper.url, 'dialog-source'));
    actions.append(actionButton(state.saved[paper.id] ? '移除书签' : '收藏这篇', () => {
      toggleSaved(paper);
      detail(paper);
    }), actionButton('复制引用', () => citation(paper)), actionButton('交给 Agent ↗', () => research(paper), true));
  }

  function renderFeatured(paper) {
    if (!paper) return;
    state.featured = paper.id;
    const featured = $('#featured');
    const label = element('span', 'featured-label', '随手翻一篇');
    label.append(element('span', '', '↙'));
    const title = element('h3', '', paper.title);
    const meta = element('p', 'featured-meta', `${topicLabel(paper.topics[0])} / ${dateLabel(paper.published)} / ${paper.source}`);
    const read = element('button', 'featured-read', '翻开这一页 ↗');
    read.type = 'button';
    read.addEventListener('click', () => detail(paper));
    featured.replaceChildren(label, title, meta, read);
  }

  function paperCard(paper) {
    const card = element('article', 'paper-card');
    card.dataset.paperId = paper.id;
    const titleId = `title-${paper.id}`;
    card.setAttribute('aria-labelledby', titleId);
    const top = element('div', 'paper-top');
    const displayTopic = state.topic !== 'all' && paper.topics.includes(state.topic) ? state.topic : paper.topics[0];
    const tag = element('span', 'paper-tag', topicLabel(displayTopic));
    tag.dataset.topic = displayTopic;
    const save = element('button', 'save-button');
    save.innerHTML = icons.bookmark;
    save.type = 'button';
    save.setAttribute('aria-label', `${state.saved[paper.id] ? '取消收藏' : '收藏'}：${paper.title}`);
    save.setAttribute('aria-pressed', state.saved[paper.id] ? 'true' : 'false');
    save.addEventListener('click', () => toggleSaved(paper));
    top.append(tag, save);
    const title = element('h3', 'paper-title');
    title.id = titleId;
    const titleButton = element('a', '', paper.title);
    titleButton.href = `#paper-${paper.id}`;
    titleButton.addEventListener('click', (event) => { event.preventDefault(); detail(paper); });
    title.append(titleButton);
    const names = element('p', 'paper-authors', authors(paper));
    names.title = paper.authors.join(', ');
    const abstract = element('p', 'paper-abstract', paper.abstract || '来源未提供摘要，去原文页面看看，或交给 Agent 继续读。');
    const meta = element('div', 'paper-meta');
    meta.append(element('span', 'paper-kind', paper.kind === 'preprint' ? '预印本' : '出版文献'),
      element('span', '', `${dateLabel(paper.published)} · ${paper.source}`));
    const venue = element('span', 'venue', paper.venue && paper.venue !== paper.source ? paper.venue : '');
    venue.title = paper.venue;
    if (venue.textContent) meta.append(venue);
    const bottom = element('div', 'paper-bottom');
    const original = externalLink('原文 ↗', paper.url, 'source-action');
    const cite = element('button', 'citation-action');
    cite.type = 'button';
    cite.innerHTML = icons.copy;
    cite.append(document.createTextNode('引用'));
    cite.addEventListener('click', () => citation(paper));
    const agent = element('button', 'agent-action', '交给 Agent');
    agent.type = 'button';
    agent.insertAdjacentHTML('beforeend', icons.arrow);
    agent.addEventListener('click', () => research(paper));
    bottom.append(original, cite, agent);
    card.append(top, title, names, abstract, meta, bottom);
    return card;
  }

  function allAvailablePapers() {
    if (!state.savedOnly) return state.papers;
    const current = new Map(state.papers.map(p => [p.id, p]));
    return Object.values(state.saved).map(p => current.get(p.id) || p);
  }

  function filteredPapers() {
    const query = state.query.trim().toLocaleLowerCase();
    const filtered = allAvailablePapers().filter(p =>
      (state.topic === 'all' || p.topics.includes(state.topic))
      && (state.source === 'all' || p.source === state.source)
      && (!query || [p.title, p.abstract, p.venue, ...p.authors, ...(p.keywords || [])]
        .filter(Boolean).join(' ').toLocaleLowerCase().includes(query)));
    return filtered.sort((a, b) => state.sort === 'title' ? a.title.localeCompare(b.title)
      : (b.published || '').localeCompare(a.published || '') || a.title.localeCompare(b.title));
  }

  function render() {
    const filtered = filteredPapers();
    const savedCount = Object.keys(state.saved).length;
    $('#saved-count').textContent = String(savedCount);
    $('#saved-toggle').setAttribute('aria-pressed', state.savedOnly ? 'true' : 'false');
    $('#saved-banner').hidden = !state.savedOnly;
    $('#export-bib').disabled = savedCount === 0;
    $('#collection-count').textContent = `${state.savedOnly ? '书签' : '书单'} / ${filtered.length} 篇`;
    $('#papers').replaceChildren(...filtered.slice(0, state.visible).map(paperCard));
    $('#papers').setAttribute('aria-busy', 'false');
    $('#empty-state').hidden = !state.ready || filtered.length > 0;
    $('#empty-title').textContent = state.savedOnly && savedCount === 0 ? '给好奇心，留一枚书签。' : '这一页暂时还空着';
    $('#empty-copy').textContent = state.savedOnly && savedCount === 0
      ? '点击论文右上角的书签，下次就能从这里接着读。' : '试试换个关键词，或看看其他主题。';
    $('#load-more').hidden = filtered.length <= state.visible;
    for (const button of $('#topic-filters').children) {
      button.setAttribute('aria-pressed', button.dataset.topic === state.topic ? 'true' : 'false');
    }
  }

  function resetFilters() {
    state.query = ''; state.topic = 'all'; state.source = 'all'; state.savedOnly = false; state.visible = 12;
    $('#search').value = ''; $('#source').value = 'all';
    render();
  }

  function savedMode(value) {
    state.savedOnly = value; state.query = ''; state.topic = 'all'; state.source = 'all'; state.visible = 12;
    $('#search').value = ''; $('#source').value = 'all';
    render();
    $('#library').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
  }

  function downloadBibliography() {
    const papers = allAvailablePapers();
    const content = papers.map(p => p.citations.bibtex).filter(Boolean).join('\n\n');
    if (!content) { toast('先收藏一篇论文，再来带走引用。'); return; }
    const url = URL.createObjectURL(new Blob([content + '\n'], { type: 'application/x-bibtex;charset=utf-8' }));
    const link = element('a');
    link.href = url;
    link.download = 'papercash-reading-list.bib';
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast('已导出收藏论文的 BibTeX。');
  }

  function bindEvents() {
    $('#setup-button').addEventListener('click', setup);
    $('#bottom-setup').addEventListener('click', setup);
    $('#saved-toggle').addEventListener('click', () => savedMode(!state.savedOnly));
    $('#show-all').addEventListener('click', () => savedMode(false));
    $('#reset-filters').addEventListener('click', resetFilters);
    $('#search').addEventListener('input', event => { state.query = event.target.value; state.visible = 12; render(); });
    $('#sort').addEventListener('change', event => { state.sort = event.target.value; render(); });
    $('#source').addEventListener('change', event => { state.source = event.target.value; state.visible = 12; render(); });
    $('#load-more').addEventListener('click', () => { state.visible += 12; render(); });
    $('#export-bib').addEventListener('click', downloadBibliography);
    $('#shuffle-button').addEventListener('click', () => {
      const pool = state.papers.filter(p => p.id !== state.featured);
      renderFeatured(pool[Math.floor(Math.random() * pool.length)] || state.papers[0]);
    });
    $('#dialog-close').addEventListener('click', () => $('#paper-dialog').close());
    $('#paper-dialog').addEventListener('click', event => {
      if (event.target === $('#paper-dialog')) {
        const box = event.target.getBoundingClientRect();
        if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) event.target.close();
      }
    });
    document.addEventListener('keydown', event => {
      if (event.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName) && !$('#paper-dialog').open) {
        event.preventDefault(); $('#search').focus();
      }
    });
    window.addEventListener('storage', event => { if (event.key === STORAGE_KEY) { state.saved = loadSaved(); render(); } });
  }

  async function start() {
    state.saved = loadSaved();
    bindEvents();
    try {
      const response = await fetch('data/papers.json', { cache: 'no-cache' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const snapshot = await response.json();
      if (snapshot.schema_version !== 1 || !Array.isArray(snapshot.papers) || !Array.isArray(snapshot.topics)) throw new Error('Invalid snapshot');
      state.papers = snapshot.papers.filter(validPaper);
      if (!state.papers.length) throw new Error('Empty snapshot');
      state.topics = snapshot.topics;
      state.ready = true;
      for (const topic of [{ id: 'all', label: '全部论文' }, ...state.topics]) {
        const button = element('button', 'topic-button', topic.label);
        button.type = 'button'; button.dataset.topic = topic.id;
        button.addEventListener('click', () => { state.topic = topic.id; state.visible = 12; render(); });
        $('#topic-filters').append(button);
      }
      const feeds = Array.isArray(snapshot.feeds) ? snapshot.feeds : [];
      const degraded = feeds.filter(f => f.status !== 'ok');
      // Report the data freshness rather than the timestamp of a failed refresh attempt.
      const newest = feeds.map(f => f.updated_at).filter(Boolean).sort().at(-1);
      $('#snapshot-note').textContent = `${state.papers.length} 篇论文 · 数据更新 ${timestamp(newest || snapshot.generated_at)}${degraded.length ? ' · 部分来源延迟' : ''}`;
      $('#data-summary').textContent = `· ${feeds.length} 组主题来源`;
      for (const feed of feeds) {
        const status = feed.status === 'ok' ? '已更新' : feed.status === 'stale' ? '沿用上次数据' : '暂不可用';
        $('#feed-status').append(element('li', '', `${feed.source} / ${topicLabel(feed.topic)}：${status}，${feed.count} 篇；${timestamp(feed.updated_at)}`));
      }
      $('#data-disclosure').textContent = degraded.length ? '部分来源本次未能取得新数据，已标明状态并保留可用的旧书单。' : '';
      $('#load-state').hidden = true;
      render();
      renderFeatured(state.papers.find(p => p.abstract) || state.papers[0]);
    } catch {
      $('#snapshot-note').textContent = '书单暂时没能加载，请稍后再试。';
      $('#load-state').textContent = '书单加载失败。刷新页面重试，或先把 PaperCash 交给你的 Agent。';
      $('#papers').setAttribute('aria-busy', 'false');
      $('#collection-count').textContent = '暂时无法加载';
      $('#featured').replaceChildren(element('span', 'featured-label', '先留一点位置给好奇心'),
        element('p', 'featured-loading', '书单暂时没有翻开。'), actionButton('交给 Agent 开始研究 ↗', setup));
      $('#shuffle-button').disabled = true;
    }
  }

  start();
})();
