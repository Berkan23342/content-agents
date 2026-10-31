import React from 'react';
import {AbsoluteFill, Audio, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {loadFont as loadDisplay} from '@remotion/google-fonts/LilitaOne';
import {loadFont as loadBody} from '@remotion/google-fonts/Nunito';

const display = loadDisplay('normal', {weights: ['400'], subsets: ['latin']}).fontFamily;
const body = loadBody('normal', {weights: ['800', '900'], subsets: ['latin']}).fontFamily;

// ---------------------------------------------------------------- props (written by scripts/quiz.py)
// A vertical 1080x1920 Short: a hook, five questions, then "comment your score".
// Everything important stays inside x 100-960, y 90-1520: YouTube draws its buttons and the title over the rest.
export type Question = {
	type: 'question';
	from: number;
	duration: number;
	kind: 'choice' | 'flag' | 'math' | 'tf';
	n: number;
	text: string;
	flag?: string | null;
	options: string[];
	answer: number;
	timerAt: number;
	timerLen: number;
	revealAt: number;
	note?: string | null;
};
type Hook = {type: 'hook'; from: number; duration: number; title: string[]; sub: string};
type End = {type: 'end'; from: number; duration: number};
export type QuizScene = Hook | Question | End;
export type Theme = {a: string; b: string; accent: string};

export type QuizProps = {durationInFrames: number; audio: string; theme: Theme; total: number; scenes: QuizScene[]};

const INK = '#1f1b3a';
const GREEN = '#22C55E';
const RED = '#EF4444';
const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const hash = (n: number) => {
	const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
	return x - Math.floor(x);
};

const heading = (size: number, color = '#ffffff'): React.CSSProperties => ({
	fontFamily: display,
	fontSize: size,
	color,
	lineHeight: 1.02,
	textShadow: '0 8px 0 rgba(0,0,0,0.22)',
});

// ---------------------------------------------------------------- brand
/** The Brain Snack mascot: a pink brain with a bite taken out of it. */
export const BrainLogo: React.FC<{size: number; blink?: number}> = ({size, blink = 1}) => (
	<svg width={size} height={size * 0.86} viewBox="0 0 120 103" style={{overflow: 'visible'}}>
		<defs>
			<mask id="bite">
				<rect x={-10} y={-10} width={140} height={130} fill="#fff" />
				<circle cx={104} cy={18} r={15} fill="#000" />
				<circle cx={114} cy={36} r={11} fill="#000" />
			</mask>
		</defs>
		<g mask="url(#bite)">
			<g fill="#FF8FB8" stroke="#D9467F" strokeWidth={4}>
				<circle cx={36} cy={46} r={28} />
				<circle cx={60} cy={32} r={28} />
				<circle cx={84} cy={46} r={28} />
				<circle cx={46} cy={68} r={26} />
				<circle cx={74} cy={68} r={26} />
			</g>
			<g fill="#FF8FB8">
				<circle cx={60} cy={52} r={30} />
			</g>
			<path d="M60 22 Q52 40 60 52 Q68 64 60 84" stroke="#D9467F" strokeWidth={4} fill="none" strokeLinecap="round" />
			<path d="M28 40 Q38 36 40 46 M80 34 Q90 32 92 42" stroke="#D9467F" strokeWidth={3.5} fill="none" strokeLinecap="round" />
		</g>
		<ellipse cx={47} cy={60} rx={7} ry={9 * blink} fill={INK} />
		<ellipse cx={73} cy={60} rx={7} ry={9 * blink} fill={INK} />
		<circle cx={49} cy={57} r={2.4} fill="#fff" opacity={blink > 0.5 ? 1 : 0} />
		<circle cx={75} cy={57} r={2.4} fill="#fff" opacity={blink > 0.5 ? 1 : 0} />
		<path d="M52 74 Q60 82 68 74" stroke={INK} strokeWidth={4} fill="none" strokeLinecap="round" />
		<ellipse cx={38} cy={72} rx={6} ry={4} fill="#FF5C9A" opacity={0.6} />
		<ellipse cx={82} cy={72} rx={6} ry={4} fill="#FF5C9A" opacity={0.6} />
	</svg>
);

const blinkAt = (frame: number) => {
	const p = frame % 96;
	return p < 4 ? Math.abs(p - 2) / 2 + 0.1 : 1;
};

const Backdrop: React.FC<{theme: Theme}> = ({theme}) => {
	const frame = useCurrentFrame();
	return (
		<AbsoluteFill style={{background: `linear-gradient(160deg, ${theme.a} 0%, ${theme.b} 100%)`, overflow: 'hidden'}}>
			{Array.from({length: 6}, (_, i) => {
				const x = hash(i) * 1080 + Math.sin(frame / (90 + i * 17) + i) * 80;
				const y = hash(i + 7) * 1920 + Math.cos(frame / (110 + i * 13) + i) * 90;
				const r = 220 + hash(i + 3) * 260;
				return <div key={i} style={{position: 'absolute', left: x - r, top: y - r, width: r * 2, height: r * 2, borderRadius: '50%', background: 'radial-gradient(circle, rgba(255,255,255,0.16) 0%, rgba(255,255,255,0) 70%)'}} />;
			})}
			{Array.from({length: 14}, (_, i) => {
				const x = hash(i + 40) * 1000 + 40;
				const y = ((hash(i + 60) * 2200 - frame * (0.6 + hash(i) * 0.8)) % 2200 + 2200) % 2200 - 140;
				return (
					<span key={`q${i}`} style={{position: 'absolute', left: x, top: y, ...heading(60 + hash(i + 9) * 70), textShadow: 'none', opacity: 0.1, transform: `rotate(${(hash(i + 2) - 0.5) * 50 + frame * 0.2}deg)`}}>
						{i % 3 ? '?' : '!'}
					</span>
				);
			})}
		</AbsoluteFill>
	);
};

const Brand: React.FC = () => {
	const frame = useCurrentFrame();
	return (
		<div style={{position: 'absolute', top: 92, width: '100%', display: 'flex', justifyContent: 'center'}}>
			<div style={{display: 'flex', alignItems: 'center', gap: 14, padding: '8px 30px 8px 16px', borderRadius: 50, background: 'rgba(255,255,255,0.16)', border: '3px solid rgba(255,255,255,0.35)'}}>
				<BrainLogo size={62} blink={blinkAt(frame)} />
				<span style={{...heading(42), textShadow: 'none', letterSpacing: 1}}>BRAIN SNACK QUIZ</span>
			</div>
		</div>
	);
};

const Progress: React.FC<{done: number; current: number; total: number; accent: string}> = ({done, current, total, accent}) => {
	const frame = useCurrentFrame();
	return (
		<div style={{position: 'absolute', top: 196, width: '100%', display: 'flex', justifyContent: 'center', gap: 12}}>
			{Array.from({length: total}, (_, i) => (
				<div
					key={i}
					style={{
						width: 132,
						height: 16,
						borderRadius: 8,
						background: i < done ? '#ffffff' : i === current ? accent : 'rgba(255,255,255,0.25)',
						opacity: i === current && i >= done ? 0.7 + 0.3 * Math.sin(frame / 5) : 1,
					}}
				/>
			))}
		</div>
	);
};

// ---------------------------------------------------------------- scenes
const HookScene: React.FC<{scene: Hook; theme: Theme}> = ({scene, theme}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const out = clamp((frame - (scene.duration - 8)) / 8);
	const logo = spring({frame, fps, config: {damping: 9, stiffness: 120}});
	return (
		<AbsoluteFill style={{opacity: 1 - out}}>
			<div style={{position: 'absolute', top: 360, width: '100%', display: 'flex', justifyContent: 'center', transform: `scale(${logo}) translateY(${Math.sin(frame / 7) * 12}px) rotate(${Math.sin(frame / 11) * 5}deg)`}}>
				<BrainLogo size={380} blink={blinkAt(frame + 40)} />
			</div>
			{scene.title.map((line, i) => {
				const s = spring({frame: frame - 5 - i * 5, fps, config: {damping: 10, stiffness: 160}});
				return (
					<div key={i} style={{position: 'absolute', top: 760 + i * 170, width: '100%', textAlign: 'center', transform: `scale(${s})`}}>
						<span style={heading(line.length > 10 ? 140 : 170)}>{line}</span>
					</div>
				);
			})}
			<div
				style={{
					position: 'absolute',
					top: 780 + scene.title.length * 170 + 30,
					width: '100%',
					display: 'flex',
					justifyContent: 'center',
					transform: `scale(${spring({frame: frame - 16, fps, config: {damping: 9}})}) rotate(-3deg)`,
				}}
			>
				<span style={{...heading(70, INK), textShadow: 'none', background: theme.accent, padding: '14px 40px', borderRadius: 40, boxShadow: '0 8px 0 rgba(0,0,0,0.2)'}}>{scene.sub}</span>
			</div>
		</AbsoluteFill>
	);
};

const textSize = (s: string) => (s.length < 34 ? 88 : s.length < 60 ? 78 : s.length < 90 ? 68 : 58);

const Timer: React.FC<{q: Question; color: string}> = ({q, color}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const r = 64;
	const c = 2 * Math.PI * r;
	const left = clamp(1 - (frame - q.timerAt) / q.timerLen);
	const revealed = frame >= q.revealAt;
	const secs = Math.ceil(left * (q.timerLen / fps) - 0.001);
	const pop = frame >= q.timerAt && !revealed ? 1 + 0.12 * Math.exp(-((frame - q.timerAt) % fps) / 4) : 1;
	const ring = revealed ? GREEN : left < 0.34 ? RED : color;
	return (
		<div style={{position: 'absolute', left: 540 - 84, top: 880 - 84, width: 168, height: 168, transform: `scale(${pop})`}}>
			<svg width={168} height={168} viewBox="-84 -84 168 168">
				<circle r={80} fill="#ffffff" />
				<circle r={r} fill="none" stroke="#e7e6f2" strokeWidth={16} />
				<circle r={r} fill="none" stroke={ring} strokeWidth={16} strokeLinecap="round" strokeDasharray={`${c * (revealed ? 1 : left)} ${c}`} transform="rotate(-90)" />
				{revealed ? <path d="M-30 2 L-8 24 L32 -20" stroke={GREEN} strokeWidth={16} fill="none" strokeLinecap="round" strokeLinejoin="round" transform={`scale(${spring({frame: frame - q.revealAt, fps, config: {damping: 9}})})`} /> : null}
			</svg>
			{revealed ? null : (
				<div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
					<span style={{fontFamily: display, fontSize: 84, color: INK}}>{frame < q.timerAt ? '?' : Math.max(1, secs)}</span>
				</div>
			)}
		</div>
	);
};

const Card: React.FC<{q: Question; theme: Theme; total: number}> = ({q, theme, total}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const s = spring({frame, fps, config: {damping: 12, stiffness: 140}});
	return (
		<div style={{position: 'absolute', left: 80, top: 262, width: 920, height: 620, transform: `scale(${s})`, transformOrigin: '50% 60%'}}>
			<div style={{position: 'absolute', inset: 0, borderRadius: 56, background: '#ffffff', boxShadow: '0 22px 0 rgba(0,0,0,0.18)'}} />
			<div style={{position: 'absolute', top: 34, width: '100%', display: 'flex', justifyContent: 'center'}}>
				<span style={{fontFamily: body, fontWeight: 900, fontSize: 34, letterSpacing: 2, color: '#ffffff', background: theme.a, padding: '8px 26px', borderRadius: 30}}>
					QUESTION {q.n}/{total}
				</span>
			</div>
			{q.kind === 'flag' && q.flag ? (
				<div style={{position: 'absolute', left: 160, top: 120, width: 600, height: 450, borderRadius: 22, overflow: 'hidden', border: '6px solid #ececf4', boxShadow: '0 10px 0 rgba(0,0,0,0.08)'}}>
					<Img src={staticFile(q.flag)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
				</div>
			) : (
				<div style={{position: 'absolute', left: 60, right: 60, top: 110, bottom: 90, display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center'}}>
					{q.kind === 'math' ? (
						<span style={{fontFamily: display, fontSize: q.text.length > 16 ? 100 : q.text.length > 10 ? 124 : 150, color: INK, lineHeight: 1.1}}>{q.text}</span>
					) : (
						<span style={{fontFamily: body, fontWeight: 900, fontSize: textSize(q.text), color: INK, lineHeight: 1.18}}>{q.text}</span>
					)}
				</div>
			)}
		</div>
	);
};

const Options: React.FC<{q: Question; theme: Theme}> = ({q, theme}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const revealed = frame >= q.revealAt;
	const pulse = revealed ? 1 + 0.07 * Math.exp(-(frame - q.revealAt) / 6) * Math.cos((frame - q.revealAt) / 2) : 1;
	if (q.kind === 'tf') {
		return (
			<>
				{q.options.map((o, i) => {
					const s = spring({frame: frame - 6 - i * 4, fps, config: {damping: 11, stiffness: 150}});
					const right = i === q.answer;
					return (
						<div
							key={i}
							style={{
								position: 'absolute',
								left: i === 0 ? 140 : 560,
								top: 1030,
								width: 380,
								height: 210,
								borderRadius: 48,
								background: i === 0 ? GREEN : RED,
								boxShadow: revealed && right ? '0 0 0 12px #ffffff, 0 16px 0 rgba(0,0,0,0.2)' : '0 16px 0 rgba(0,0,0,0.2)',
								opacity: revealed && !right ? 0.35 : 1,
								transform: `scale(${s * (revealed && right ? pulse : revealed ? 0.94 : 1)})`,
								display: 'flex',
								alignItems: 'center',
								justifyContent: 'center',
							}}
						>
							<span style={heading(96)}>{o}</span>
						</div>
					);
				})}
				{q.note && revealed ? (
					<div style={{position: 'absolute', left: 120, width: 840, top: 1300, display: 'flex', justifyContent: 'center', transform: `scale(${spring({frame: frame - q.revealAt - 6, fps, config: {damping: 11}})})`}}>
						<span style={{fontFamily: body, fontWeight: 800, fontSize: 52, color: INK, background: 'rgba(255,255,255,0.95)', padding: '18px 34px', borderRadius: 34, textAlign: 'center', lineHeight: 1.2}}>{q.note}</span>
					</div>
				) : null}
			</>
		);
	}
	return (
		<>
			{q.options.map((o, i) => {
				const s = spring({frame: frame - 6 - i * 3, fps, config: {damping: 12, stiffness: 150}});
				const right = i === q.answer;
				const x = interpolate(s, [0, 1], [700, 0]);
				return (
					<div
						key={i}
						style={{
							position: 'absolute',
							left: 140,
							top: 1010 + i * 136,
							width: 800,
							height: 114,
							borderRadius: 57,
							background: revealed && right ? GREEN : '#ffffff',
							boxShadow: '0 10px 0 rgba(0,0,0,0.18)',
							opacity: (revealed && !right ? 0.45 : 1) * s,
							transform: `translateX(${x}px) scale(${revealed && right ? pulse : revealed ? 0.96 : 1})`,
							display: 'flex',
							alignItems: 'center',
						}}
					>
						<div
							style={{
								width: 86,
								height: 86,
								marginLeft: 14,
								borderRadius: 43,
								background: revealed && right ? '#ffffff' : theme.a,
								display: 'flex',
								alignItems: 'center',
								justifyContent: 'center',
								flexShrink: 0,
							}}
						>
							<span style={{fontFamily: display, fontSize: 52, color: revealed && right ? GREEN : '#ffffff'}}>{'ABCD'[i]}</span>
						</div>
						<span
							style={{
								fontFamily: body,
								fontWeight: 900,
								fontSize: o.length > 22 ? 40 : o.length > 16 ? 46 : 52,
								color: revealed && right ? '#ffffff' : INK,
								marginLeft: 28,
								whiteSpace: 'nowrap',
							}}
						>
							{o}
						</span>
					</div>
				);
			})}
		</>
	);
};

const Burst: React.FC<{at: number; x: number; y: number}> = ({at, x, y}) => {
	const frame = useCurrentFrame();
	const t = frame - at;
	if (t < 0 || t > 40) return null;
	const colors = ['#FACC15', '#22D3EE', '#ffffff', '#F472B6', '#4ADE80'];
	return (
		<svg style={{position: 'absolute', inset: 0, overflow: 'visible'}} width={1080} height={1920}>
			{Array.from({length: 28}, (_, i) => {
				const a = hash(i + at) * Math.PI * 2;
				const v = 16 + hash(i * 5 + at) * 18;
				const px = x + Math.cos(a) * v * t;
				const py = y + Math.sin(a) * v * t * 0.8 + 0.45 * t * t;
				return <rect key={i} x={px - 9} y={py - 6} width={18} height={12} rx={3} fill={colors[i % colors.length]} opacity={clamp((40 - t) / 14)} transform={`rotate(${t * 11 + i * 33} ${px} ${py})`} />;
			})}
		</svg>
	);
};

const QuestionScene: React.FC<{q: Question; theme: Theme; total: number}> = ({q, theme, total}) => {
	const frame = useCurrentFrame();
	const out = clamp((frame - (q.duration - 8)) / 8);
	return (
		<AbsoluteFill style={{opacity: 1 - out, transform: `translateX(${-out * 120}px)`}}>
			<Card q={q} theme={theme} total={total} />
			<Options q={q} theme={theme} />
			<Timer q={q} color={theme.a} />
			<Burst at={q.revealAt} x={540} y={q.kind === 'tf' ? 1130 : 1010 + q.answer * 136 + 57} />
		</AbsoluteFill>
	);
};

const EndScene: React.FC<{scene: End; theme: Theme}> = ({scene, theme}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const lines = ['HOW MANY', 'DID YOU', 'GET?'];
	const arrow = spring({frame: frame - 24, fps, config: {damping: 10}});
	return (
		<AbsoluteFill>
			<div style={{position: 'absolute', top: 300, width: '100%', display: 'flex', justifyContent: 'center', transform: `scale(${spring({frame, fps, config: {damping: 9}})})`}}>
				<BrainLogo size={260} blink={blinkAt(frame + 20)} />
			</div>
			{lines.map((l, i) => (
				<div key={l} style={{position: 'absolute', top: 580 + i * 150, width: '100%', textAlign: 'center', transform: `scale(${spring({frame: frame - 4 - i * 4, fps, config: {damping: 10}})})`}}>
					<span style={heading(150)}>{l}</span>
				</div>
			))}
			<div style={{position: 'absolute', top: 1090, width: '100%', display: 'flex', justifyContent: 'center', gap: 16}}>
				{[0, 1, 2, 3, 4, 5].map((k) => (
					<div
						key={k}
						style={{
							width: 104,
							height: 104,
							borderRadius: 52,
							background: '#ffffff',
							display: 'flex',
							alignItems: 'center',
							justifyContent: 'center',
							transform: `scale(${spring({frame: frame - 12 - k * 3, fps, config: {damping: 9}})})`,
							boxShadow: '0 8px 0 rgba(0,0,0,0.18)',
						}}
					>
						<span style={{fontFamily: display, fontSize: 60, color: k === 5 ? GREEN : theme.a}}>{k}</span>
					</div>
				))}
			</div>
			<div style={{position: 'absolute', top: 1270, width: '100%', display: 'flex', justifyContent: 'center', transform: `scale(${spring({frame: frame - 18, fps, config: {damping: 9}})}) rotate(-2deg)`}}>
				<span style={{...heading(62, INK), textShadow: 'none', background: theme.accent, padding: '14px 36px', borderRadius: 40, boxShadow: '0 8px 0 rgba(0,0,0,0.2)'}}>COMMENT YOUR SCORE!</span>
			</div>
			<svg style={{position: 'absolute', left: 760, top: 1360, opacity: arrow, transform: `translate(${Math.sin(frame / 4) * 8}px, ${Math.sin(frame / 4) * 8}px)`}} width={190} height={190} viewBox="0 0 190 190">
				<path d="M20 20 Q120 30 150 140" stroke="#ffffff" strokeWidth={16} fill="none" strokeLinecap="round" />
				<path d="M112 128 L152 150 L168 104" stroke="#ffffff" strokeWidth={16} fill="none" strokeLinecap="round" strokeLinejoin="round" />
			</svg>
		</AbsoluteFill>
	);
};

// ---------------------------------------------------------------- composition
export const Quiz: React.FC<QuizProps> = ({scenes, audio, theme, total}) => {
	const frame = useCurrentFrame();
	const questions = scenes.filter((s): s is Question => s.type === 'question');
	const done = questions.filter((q) => frame >= q.from + q.revealAt).length;
	const current = questions.filter((q) => frame >= q.from).length - 1;
	const inQuiz = current >= 0 && scenes.some((s) => s.type === 'question' && frame >= s.from && frame < s.from + s.duration);
	return (
		<AbsoluteFill style={{fontFamily: body}}>
			<Backdrop theme={theme} />
			{scenes.map((s, i) => (
				<Sequence key={i} from={s.from} durationInFrames={s.duration}>
					{s.type === 'hook' && <HookScene scene={s} theme={theme} />}
					{s.type === 'question' && <QuestionScene q={s} theme={theme} total={total} />}
					{s.type === 'end' && <EndScene scene={s} theme={theme} />}
				</Sequence>
			))}
			<Brand />
			{inQuiz ? <Progress done={done} current={current} total={total} accent={theme.accent} /> : null}
			{audio ? <Audio src={staticFile(audio)} /> : null}
		</AbsoluteFill>
	);
};
