use std::collections::VecDeque;
use std::time::{Duration, Instant};

use crossterm::event::{self, Event, KeyCode, KeyEventKind, MouseEventKind};
use crossterm::terminal::{self, EnterAlternateScreen, LeaveAlternateScreen};
use ratatui::layout::{Alignment, Constraint, Direction, Layout, Rect};
use ratatui::style::{Color, Modifier, Style, Stylize};
use ratatui::symbols;
use ratatui::text::{Line, Span};
use ratatui::widgets::{
    block::Title, Block, BorderType, Borders, Cell, Chart, Dataset, Gauge, GraphType,
    List, ListItem, ListState, Paragraph, Row, Table, TableState, Tabs, Wrap,
};
use ratatui::Frame;
use ratatui::{prelude::*, Terminal};

const AGENT_COLORS: &[(&str, Color)] = &[
    ("claude", Color::Rgb(255, 140, 0)),
    ("aider", Color::Cyan),
    ("gemini", Color::Rgb(147, 112, 219)),
    ("opencode", Color::Green),
    ("codex", Color::Rgb(0, 200, 200)),
    ("copilot", Color::Rgb(100, 200, 255)),
    ("ollama", Color::Rgb(255, 200, 0)),
];

#[derive(Clone)]
struct LogEntry {
    timestamp: String,
    text: String,
    level: LogLevel,
}

#[derive(Clone, PartialEq)]
enum LogLevel {
    Info,
    Success,
    Warning,
    Error,
    Security,
    Permission,
}

impl LogLevel {
    fn color(&self) -> Color {
        match self {
            LogLevel::Info => Color::Cyan,
            LogLevel::Success => Color::Green,
            LogLevel::Warning => Color::Yellow,
            LogLevel::Error => Color::Red,
            LogLevel::Security => Color::Rgb(255, 69, 0),
            LogLevel::Permission => Color::Magenta,
        }
    }

    fn icon(&self) -> &'static str {
        match self {
            LogLevel::Info => "[i]",
            LogLevel::Success => "[✓]",
            LogLevel::Warning => "[!]",
            LogLevel::Error => "[✗]",
            LogLevel::Security => "[⚠]",
            LogLevel::Permission => "[?]",
        }
    }
}

#[derive(Clone)]
struct AgentState {
    name: String,
    status: AgentStatus,
    role: String,
    token_usage: u64,
    current_action: String,
}

#[derive(Clone, PartialEq)]
enum AgentStatus {
    Active,
    Waiting,
    Failed,
    Reasoning,
    Reviewing,
    Idle,
}

impl AgentStatus {
    fn color(&self) -> Color {
        match self {
            AgentStatus::Active => Color::Green,
            AgentStatus::Waiting => Color::Yellow,
            AgentStatus::Failed => Color::Red,
            AgentStatus::Reasoning => Color::Cyan,
            AgentStatus::Reviewing => Color::Magenta,
            AgentStatus::Idle => Color::DarkGray,
        }
    }

    fn as_str(&self) -> &'static str {
        match self {
            AgentStatus::Active => "ACTIVE",
            AgentStatus::Waiting => "WAIT",
            AgentStatus::Failed => "FAIL",
            AgentStatus::Reasoning => "REASON",
            AgentStatus::Reviewing => "REVIEW",
            AgentStatus::Idle => "IDLE",
        }
    }
}

#[derive(Clone)]
struct PermissionRequest {
    agent: String,
    command: String,
    risk_level: String,
    description: Vec<String>,
}

struct App {
    agents: Vec<AgentState>,
    logs: VecDeque<LogEntry>,
    events: VecDeque<LogEntry>,
    sidebar_scroll: u16,
    activity_scroll: u16,
    event_scroll: u16,
    selected_agent: usize,
    show_permission: bool,
    permission: Option<PermissionRequest>,
    start_time: Instant,
    session_id: String,
    total_tasks: u32,
    completed_tasks: u32,
    total_tokens: u64,
    saved_tokens: u64,
    tab_index: usize,
    running: bool,
    agent_sig: String,
    plan_file: String,
}

impl App {
    fn new() -> Self {
        let mut app = App {
            agents: Vec::new(),
            logs: VecDeque::with_capacity(1000),
            events: VecDeque::with_capacity(500),
            sidebar_scroll: 0,
            activity_scroll: 0,
            event_scroll: 0,
            selected_agent: 0,
            show_permission: false,
            permission: None,
            start_time: Instant::now(),
            session_id: format!("ses_{}", uuid_v4()),
            total_tasks: 0,
            completed_tasks: 0,
            total_tokens: 0,
            saved_tokens: 0,
            tab_index: 0,
            running: true,
            agent_sig: String::new(),
            plan_file: String::new(),
        };
        app.seed_demo_data();
        app
    }

    fn seed_demo_data(&mut self) {
        self.agents = vec![
            AgentState {
                name: "opencode".into(),
                status: AgentStatus::Active,
                role: "Frontend".into(),
                token_usage: 1250,
                current_action: "Generating React components...".into(),
            },
            AgentState {
                name: "gemini".into(),
                status: AgentStatus::Reasoning,
                role: "Backend".into(),
                token_usage: 3400,
                current_action: "Designing API schema...".into(),
            },
            AgentState {
                name: "codex".into(),
                status: AgentStatus::Waiting,
                role: "Debugger".into(),
                token_usage: 800,
                current_action: "Awaiting backend output...".into(),
            },
            AgentState {
                name: "claude".into(),
                status: AgentStatus::Idle,
                role: "Reviewer".into(),
                token_usage: 0,
                current_action: "Standing by".into(),
            },
        ];

        self.logs.push_back(LogEntry {
            timestamp: "10:42:11".into(),
            text: "opencode analyzing frontend requirements...".into(),
            level: LogLevel::Info,
        });
        self.logs.push_back(LogEntry {
            timestamp: "10:42:18".into(),
            text: "Dependency graph validated — 4 tasks ready".into(),
            level: LogLevel::Success,
        });
        self.logs.push_back(LogEntry {
            timestamp: "10:42:30".into(),
            text: "gemini generating backend scaffold...".into(),
            level: LogLevel::Info,
        });
        self.logs.push_back(LogEntry {
            timestamp: "10:42:31".into(),
            text: "opencode → src/App.jsx created (2.4 KB)".into(),
            level: LogLevel::Success,
        });
        self.logs.push_back(LogEntry {
            timestamp: "10:42:34".into(),
            text: "cargo test failed — 3 compiler errors".into(),
            level: LogLevel::Error,
        });
        self.logs.push_back(LogEntry {
            timestamp: "10:42:35".into(),
            text: "Surgical repair initiated by codex".into(),
            level: LogLevel::Warning,
        });
        self.logs.push_back(LogEntry {
            timestamp: "10:42:40".into(),
            text: "SECURITY: aider requesting git commit access".into(),
            level: LogLevel::Security,
        });
        self.logs.push_back(LogEntry {
            timestamp: "10:42:45".into(),
            text: "PERMISSION: package install requested (express)".into(),
            level: LogLevel::Permission,
        });
    }

    fn elapsed_str(&self) -> String {
        let d = self.start_time.elapsed();
        format!("{:02}:{:02}:{:02}", d.as_secs() / 3600, (d.as_secs() / 60) % 60, d.as_secs() % 60)
    }

    fn agent_color(&self, name: &str) -> Color {
        for (n, c) in AGENT_COLORS {
            if name.contains(n) {
                return *c;
            }
        }
        Color::Cyan
    }

    fn handle_key(&mut self, key: KeyCode) {
        match key {
            KeyCode::Char('q') => self.running = false,
            KeyCode::Char('p') => {}
            KeyCode::Char('t') => self.tab_index = (self.tab_index + 1) % 3,
            KeyCode::Char('y') => {
                if self.show_permission {
                    self.show_permission = false;
                    self.logs.push_back(LogEntry {
                        timestamp: chrono_now(),
                        text: "Permission granted — executing command".into(),
                        level: LogLevel::Success,
                    });
                }
            }
            KeyCode::Char('n') => {
                if self.show_permission {
                    self.show_permission = false;
                    self.logs.push_back(LogEntry {
                        timestamp: chrono_now(),
                        text: "Permission denied — command blocked".into(),
                        level: LogLevel::Security,
                    });
                }
            }
            KeyCode::Esc => self.show_permission = false,
            KeyCode::Up => {
                if self.selected_agent > 0 {
                    self.selected_agent -= 1;
                }
            }
            KeyCode::Down => {
                if self.selected_agent < self.agents.len().saturating_sub(1) {
                    self.selected_agent += 1;
                }
            }
            _ => {}
        }
    }
}

fn chrono_now() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let d = SystemTime::now().duration_since(UNIX_EPOCH).unwrap();
    let secs = d.as_secs();
    let h = (secs / 3600) % 24;
    let m = (secs / 60) % 60;
    let s = secs % 60;
    format!("{:02}:{:02}:{:02}", h, m, s)
}

fn uuid_v4() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let d = SystemTime::now().duration_since(UNIX_EPOCH).unwrap();
    format!("{:016x}", d.as_nanos())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    terminal::enable_raw_mode()?;
    let mut stdout = std::io::stdout();
    crossterm::execute!(stdout, EnterAlternateScreen)?;

    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let mut app = App::new();
    let tick_rate = Duration::from_millis(50);

    loop {
        terminal.draw(|f| ui(f, &mut app))?;

        if event::poll(tick_rate)? {
            if let Event::Key(key) = event::read()? {
                if key.kind == KeyEventKind::Press {
                    app.handle_key(key.code);
                    if !app.running {
                        break;
                    }
                }
            }
            if let Event::Mouse(m) = event::read()? {
                if let MouseEventKind::ScrollDown = m.kind {
                    app.activity_scroll = app.activity_scroll.saturating_add(1);
                }
                if let MouseEventKind::ScrollUp = m.kind {
                    app.activity_scroll = app.activity_scroll.saturating_sub(1);
                }
            }
            if let Event::Resize(_, _) = event::read()? {}
        }
    }

    terminal::disable_raw_mode()?;
    crossterm::execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    Ok(())
}

fn ui(frame: &mut Frame, app: &mut App) {
    let area = frame.size();
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(7),
            Constraint::Min(1),
            Constraint::Length(10),
        ])
        .split(area);

    render_header(frame, app, chunks[0]);
    render_main(frame, app, chunks[1]);
    render_event_trace(frame, app, chunks[2]);

    if app.show_permission {
        render_permission_modal(frame, app, area);
    }
}

fn render_header(frame: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Length(32), Constraint::Min(1)])
        .split(area);

    let logo = Block::default()
        .borders(Borders::ALL)
        .border_type(BorderType::Thick)
        .border_style(Style::default().fg(Color::Cyan))
        .style(Style::default().bg(Color::Rgb(11, 15, 20)));
    let logo_inner = logo.inner(chunks[0]);
    frame.render_widget(logo, chunks[0]);

    let logo_lines = vec![
        Line::from(vec![
            Span::styled("  ░░", Style::default().fg(Color::Cyan)),
        ]),
        Line::from(vec![
            Span::styled(" ░░░░░░", Style::default().fg(Color::Cyan)),
            Span::styled(" MONAD", Style::default().fg(Color::Rgb(255, 200, 0)).add_modifier(Modifier::BOLD)),
            Span::styled(" v0.1", Style::default().fg(Color::DarkGray)),
        ]),
        Line::from(vec![
            Span::styled(" ░░░▒░░", Style::default().fg(Color::Cyan)),
        ]),
        Line::from(vec![
            Span::styled("  ░░  ░░  ░░", Style::default().fg(Color::Cyan)),
        ]),
    ];
    let logo_para = Paragraph::new(logo_lines).style(Style::default().bg(Color::Rgb(11, 15, 20)));
    frame.render_widget(logo_para, logo_inner);

    let header = Block::default()
        .borders(Borders::ALL)
        .border_type(BorderType::Thick)
        .border_style(Style::default().fg(Color::Cyan))
        .style(Style::default().bg(Color::Rgb(11, 15, 20)));
    let inner = header.inner(chunks[1]);
    frame.render_widget(header, chunks[1]);

    let meta_lines = vec![
        Line::from(vec![
            Span::styled(" Session:  ", Style::default().fg(Color::DarkGray)),
            Span::styled(&app.session_id[..16], Style::default().fg(Color::Green)),
            Span::raw("  │  "),
            Span::styled("Elapsed: ", Style::default().fg(Color::DarkGray)),
            Span::styled(app.elapsed_str(), Style::default().fg(Color::Yellow)),
        ]),
        Line::from(vec![
            Span::styled(" Tasks:   ", Style::default().fg(Color::DarkGray)),
            Span::styled(
                format!("{}/{}", app.completed_tasks, app.total_tasks),
                Style::default().fg(Color::Cyan),
            ),
            Span::raw("  │  "),
            Span::styled("Tokens: ", Style::default().fg(Color::DarkGray)),
            Span::styled(format!("{}k", app.total_tokens / 1000), Style::default().fg(Color::Magenta)),
            Span::raw("  │  "),
            Span::styled("Saved: ", Style::default().fg(Color::DarkGray)),
            Span::styled(format!("{}%", (app.saved_tokens * 100) / std::cmp::max(app.total_tokens, 1)), Style::default().fg(Color::Green)),
        ]),
        Line::from(vec![
            Span::styled(" Plan:    ", Style::default().fg(Color::DarkGray)),
            Span::styled("web-app-project.jsonl", Style::default().fg(Color::Rgb(100, 200, 255))),
            Span::raw("  │  "),
            Span::styled("Status: ", Style::default().fg(Color::DarkGray)),
            Span::styled("RUNNING", Style::default().fg(Color::Green).add_modifier(Modifier::BOLD)),
        ]),
    ];
    let meta_para = Paragraph::new(meta_lines).style(Style::default().bg(Color::Rgb(11, 15, 20)));
    frame.render_widget(meta_para, inner);
}

fn render_main(frame: &mut Frame, app: &mut App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Length(32), Constraint::Min(1), Constraint::Length(36)])
        .split(area);

    render_sidebar(frame, app, chunks[0]);
    render_activity_feed(frame, app, chunks[1]);
    render_task_panel(frame, app, chunks[2]);
}

fn render_sidebar(frame: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Min(1), Constraint::Length(4)])
        .split(area);

    let block = Block::default()
        .title(" Agents ")
        .title_alignment(Alignment::Center)
        .borders(Borders::ALL)
        .border_type(BorderType::Thick)
        .border_style(Style::default().fg(Color::Cyan))
        .style(Style::default().bg(Color::Rgb(11, 15, 20)));
    let inner = block.inner(chunks[0]);
    frame.render_widget(block, chunks[0]);

    let mut items: Vec<ListItem> = Vec::new();
    for agent in &app.agents {
        let color = app.agent_color(&agent.name);
        let status_color = agent.status.color();
        let arrow = if items.len() == app.selected_agent {
            "▸ "
        } else {
            "  "
        };

        let line = vec![
            Line::from(vec![
                Span::styled(arrow, Style::default().fg(Color::Cyan)),
                Span::styled(
                    format!(" {:12}", agent.name),
                    Style::default().fg(color).add_modifier(Modifier::BOLD),
                ),
                Span::raw(" "),
                Span::styled(
                    format!("{:6}", agent.status.as_str()),
                    Style::default().fg(status_color).add_modifier(Modifier::BOLD),
                ),
            ]),
            Line::from(vec![
                Span::raw("    "),
                Span::styled(&agent.current_action, Style::default().fg(Color::DarkGray)),
            ]),
            Line::from(vec![
                Span::raw("    "),
                Span::styled("role: ", Style::default().fg(Color::DarkGray)),
                Span::styled(&agent.role, Style::default().fg(Color::Rgb(100, 200, 255))),
                Span::raw("  tokens: "),
                Span::styled(format!("{}", agent.token_usage), Style::default().fg(Color::Magenta)),
            ]),
        ];

        items.push(ListItem::new(line).style(Style::default().bg(Color::Rgb(11, 15, 20))));
    }

    let list = List::new(items).highlight_style(
        Style::default()
            .bg(Color::Rgb(20, 30, 40))
            .add_modifier(Modifier::BOLD),
    );
    frame.render_widget(list, inner);

    let bar_block = Block::default()
        .title(" Progress ")
        .title_alignment(Alignment::Center)
        .borders(Borders::ALL)
        .border_type(BorderType::Thick)
        .border_style(Style::default().fg(Color::Rgb(100, 200, 100)))
        .style(Style::default().bg(Color::Rgb(11, 15, 20)));
    let bar_inner = bar_block.inner(chunks[1]);
    frame.render_widget(bar_block, chunks[1]);

    let progress = if app.total_tasks > 0 {
        app.completed_tasks as f64 / app.total_tasks as f64
    } else {
        0.0
    };
    let gauge = Gauge::default()
        .block(Block::default().title(" Workflow ").borders(Borders::NONE))
        .gauge_style(
            Style::default()
                .fg(Color::Cyan)
                .bg(Color::Rgb(20, 30, 40))
                .add_modifier(Modifier::BOLD),
        )
        .percent((progress * 100.0) as u16)
        .label(format!("{:.0}%", progress * 100.0));
    frame.render_widget(gauge, bar_inner);
}

fn render_activity_feed(frame: &mut Frame, app: &mut App, area: Rect) {
    let block = Block::default()
        .title(" Activity Feed ")
        .title_alignment(Alignment::Center)
        .borders(Borders::ALL)
        .border_type(BorderType::Thick)
        .border_style(Style::default().fg(Color::Cyan))
        .style(Style::default().bg(Color::Rgb(11, 15, 20)));
    let inner = block.inner(area);
    frame.render_widget(block, area);

    let lines: Vec<Line> = app
        .logs
        .iter()
        .rev()
        .skip(app.activity_scroll as usize)
        .take((inner.height as usize).saturating_sub(1))
        .map(|entry| {
            let color = entry.level.color();
            Line::from(vec![
                Span::styled(
                    format!(" {} ", entry.timestamp),
                    Style::default().fg(Color::DarkGray),
                ),
                Span::styled(
                    format!("{} ", entry.level.icon()),
                    Style::default().fg(color).add_modifier(Modifier::BOLD),
                ),
                Span::styled(&entry.text, Style::default().fg(Color::Rgb(200, 210, 220))),
            ])
        })
        .collect();

    let para = Paragraph::new(lines)
        .style(Style::default().bg(Color::Rgb(11, 15, 20)))
        .scroll((0, 0));
    frame.render_widget(para, inner);
}

fn render_task_panel(frame: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Min(1), Constraint::Length(12)])
        .split(area);

    let block = Block::default()
        .title(" Current Task ")
        .title_alignment(Alignment::Center)
        .borders(Borders::ALL)
        .border_type(BorderType::Thick)
        .border_style(Style::default().fg(Color::Cyan))
        .style(Style::default().bg(Color::Rgb(11, 15, 20)));
    let inner = block.inner(chunks[0]);
    frame.render_widget(block, chunks[0]);

    if let Some(agent) = app.agents.get(app.selected_agent) {
        let color = app.agent_color(&agent.name);
        let lines = vec![
            Line::from(vec![
                Span::styled(" Active Agent: ", Style::default().fg(Color::DarkGray)),
                Span::styled(&agent.name, Style::default().fg(color).add_modifier(Modifier::BOLD)),
                Span::raw("  "),
                Span::styled(
                    agent.status.as_str(),
                    Style::default().fg(agent.status.color()).add_modifier(Modifier::BOLD),
                ),
            ]),
            Line::from(vec![
                Span::styled(" Role:         ", Style::default().fg(Color::DarkGray)),
                Span::styled(&agent.role, Style::default().fg(Color::Rgb(100, 200, 255))),
            ]),
            Line::from(vec![
                Span::styled(" Action:       ", Style::default().fg(Color::DarkGray)),
                Span::styled(&agent.current_action, Style::default().fg(Color::White)),
            ]),
            Line::from(vec![
                Span::styled(" Tokens:       ", Style::default().fg(Color::DarkGray)),
                Span::styled(format!("{}", agent.token_usage), Style::default().fg(Color::Magenta)),
            ]),
        ];
        let para = Paragraph::new(lines).style(Style::default().bg(Color::Rgb(11, 15, 20)));
        frame.render_widget(para, inner);
    }

    let files = Block::default()
        .title(" Files Changed ")
        .borders(Borders::ALL)
        .border_type(BorderType::Thick)
        .border_style(Style::default().fg(Color::Rgb(100, 200, 100)))
        .style(Style::default().bg(Color::Rgb(11, 15, 20)));
    let files_inner = files.inner(chunks[1]);
    frame.render_widget(files, chunks[1]);

    let file_lines = vec![
        Line::from(vec![
            Span::styled(" src/App.jsx", Style::default().fg(Color::Green)),
            Span::raw("         "),
            Span::styled("+24 / -3", Style::default().fg(Color::Rgb(100, 200, 100))),
        ]),
        Line::from(vec![
            Span::styled(" backend/main.py", Style::default().fg(Color::Cyan)),
            Span::raw("      "),
            Span::styled("+56 / -0", Style::default().fg(Color::Rgb(100, 200, 100))),
        ]),
        Line::from(vec![
            Span::styled(" backend/database.py", Style::default().fg(Color::Magenta)),
            Span::raw("   "),
            Span::styled("+42 / -0", Style::default().fg(Color::Rgb(100, 200, 100))),
        ]),
    ];
    let files_para = Paragraph::new(file_lines).style(Style::default().bg(Color::Rgb(11, 15, 20)));
    frame.render_widget(files_para, files_inner);
}

fn render_event_trace(frame: &mut Frame, app: &App, area: Rect) {
    let block = Block::default()
        .title(" Event Trace ")
        .title_alignment(Alignment::Center)
        .borders(Borders::ALL)
        .border_type(BorderType::Thick)
        .border_style(Style::default().fg(Color::Rgb(100, 200, 200)))
        .style(Style::default().bg(Color::Rgb(11, 15, 20)));
    let inner = block.inner(area);
    frame.render_widget(block, area);

    let lines: Vec<Line> = app
        .logs
        .iter()
        .rev()
        .skip(app.event_scroll as usize)
        .take((inner.height as usize).saturating_sub(1))
        .map(|entry| {
            let color = entry.level.color();
            Line::from(vec![
                Span::styled(
                    format!("[{}] ", entry.timestamp),
                    Style::default().fg(Color::DarkGray),
                ),
                Span::styled(
                    format!("{} ", entry.level.icon()),
                    Style::default().fg(color),
                ),
                Span::styled(&entry.text, Style::default().fg(Color::Rgb(160, 170, 180))),
            ])
        })
        .collect();

    let para = Paragraph::new(lines).style(Style::default().bg(Color::Rgb(11, 15, 20)));
    frame.render_widget(para, inner);

    let shortcuts = format!(
        " [q] quit  [↑↓] nav  [t] tabs  [y/n] approve/deny  [esc] close modal"
    );
    let shortcut_para = Paragraph::new(Span::styled(
        &shortcuts,
        Style::default().fg(Color::DarkGray),
    ))
    .style(Style::default().bg(Color::Rgb(11, 15, 20)))
    .alignment(Alignment::Center);
    frame.render_widget(
        shortcut_para,
        Rect::new(area.x, area.y + area.height - 1, area.width, 1),
    );
}

fn render_permission_modal(frame: &mut Frame, app: &App, area: Rect) {
    let modal_width = 56;
    let modal_height = 14;
    let x = (area.width.saturating_sub(modal_width)) / 2;
    let y = (area.height.saturating_sub(modal_height)) / 2;
    let modal_area = Rect::new(x, y, modal_width, modal_height);

    let block = Block::default()
        .title(" Permission Required ")
        .title_alignment(Alignment::Center)
        .borders(Borders::ALL)
        .border_type(BorderType::Thick)
        .border_style(
            Style::default()
                .fg(Color::Rgb(255, 69, 0))
                .add_modifier(Modifier::BOLD),
        )
        .style(Style::default().bg(Color::Rgb(15, 10, 10)));
    let inner = block.inner(modal_area);
    frame.render_widget(block, modal_area);

    let lines = vec![
        Line::from(vec![
            Span::styled(" Agent:  ", Style::default().fg(Color::DarkGray)),
            Span::styled("aider", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
        ]),
        Line::from(Span::raw("")),
        Line::from(vec![
            Span::styled(" Command:", Style::default().fg(Color::DarkGray)),
        ]),
        Line::from(vec![
            Span::styled(
                " git commit -m \"feat: add auth flow\"",
                Style::default().fg(Color::Yellow),
            ),
        ]),
        Line::from(Span::raw("")),
        Line::from(vec![
            Span::styled(" Risk Level: ", Style::default().fg(Color::DarkGray)),
            Span::styled("MEDIUM", Style::default().fg(Color::Rgb(255, 165, 0)).add_modifier(Modifier::BOLD)),
        ]),
        Line::from(Span::raw("")),
        Line::from(vec![
            Span::styled(" This action will:", Style::default().fg(Color::DarkGray)),
        ]),
        Line::from(vec![
            Span::styled("   • modify repository state", Style::default().fg(Color::Rgb(200, 210, 220))),
        ]),
        Line::from(vec![
            Span::styled("   • create a commit", Style::default().fg(Color::Rgb(200, 210, 220))),
        ]),
        Line::from(Span::raw("")),
        Line::from(vec![
            Span::styled(" [", Style::default().fg(Color::DarkGray)),
            Span::styled("Y", Style::default().fg(Color::Green).add_modifier(Modifier::BOLD)),
            Span::styled("] Allow Once  [", Style::default().fg(Color::DarkGray)),
            Span::styled("A", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
            Span::styled("] Always Allow  [", Style::default().fg(Color::DarkGray)),
            Span::styled("N", Style::default().fg(Color::Red).add_modifier(Modifier::BOLD)),
            Span::styled("] Deny", Style::default().fg(Color::DarkGray)),
        ]),
    ];
    let para = Paragraph::new(lines).style(Style::default().bg(Color::Rgb(15, 10, 10)));
    frame.render_widget(para, inner);
}
