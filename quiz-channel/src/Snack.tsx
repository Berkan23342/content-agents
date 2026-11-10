import React, {createContext, useContext} from 'react';
import {AbsoluteFill, Audio, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {loadFont as loadDisplay} from '@remotion/google-fonts/LilitaOne';
import {loadFont as loadBody} from '@remotion/google-fonts/Nunito';
import {loadFont as loadAnton} from '@remotion/google-fonts/Anton';
import {loadFont as loadFredoka} from '@remotion/google-fonts/Fredoka';
import {loadFont as loadBebas} from '@remotion/google-fonts/BebasNeue';
import {loadFont as loadOswald} from '@remotion/google-fonts/Oswald';
import {loadFont as loadRighteous} from '@remotion/google-fonts/Righteous';
import {loadFont as loadArchivo} from '@remotion/google-fonts/ArchivoBlack';
import {loadFont as loadElite} from '@remotion/google-fonts/SpecialElite';
import {loadFont as loadBangers} from '@remotion/google-fonts/Bangers';
import {loadFont as loadBungee} from '@remotion/google-fonts/Bungee';
import {loadFont as loadMarker} from '@remotion/google-fonts/PermanentMarker';
import {BrainLogo} from './Quiz';

const display = loadDisplay('normal', {weights: ['400'], subsets: ['latin']}).fontFamily;
const body = loadBody('normal', {weights: ['800', '900'], subsets: ['latin']}).fontFamily;
const anton = loadAnton('normal', {weights: ['400'], subsets: ['latin']}).fontFamily;
const EMOJI = '"Apple Color Emoji", "Noto Color Emoji", "Segoe UI Emoji", sans-serif';
const latin = {subsets: ['latin']};
// heading and caption fonts a look can use (scripts/snack.py LOOKS picks them per format and per snack)
const FONTS: Record<string, string> = {
	lilita: display,
	anton,
	fredoka: loadFredoka('normal', {weights: ['700'], ...latin}).fontFamily,
	bebas: loadBebas('normal', {weights: ['400'], ...latin}).fontFamily,
	oswald: loadOswald('normal', {weights: ['700'], ...latin}).fontFamily,
	righteous: loadRighteous('normal', {weights: ['400'], ...latin}).fontFamily,
	archivo: loadArchivo('normal', {weights: ['400'], ...latin}).fontFamily,
	elite: loadElite('normal', {weights: ['400'], ...latin}).fontFamily,
	bangers: loadBangers('normal', {weights: ['400'], ...latin}).fontFamily,
	bungee: loadBungee('normal', {weights: ['400'], ...latin}).fontFamily,
	marker: loadMarker('normal', {weights: ['400'], ...latin}).fontFamily,
};

// ---------------------------------------------------------------- props (written by scripts/snack.py)
// A Brain Snack: one topic told in about a minute. "why" explains a question, "mystery" is a riddle told as a story,
// "real" is a real-life what-would-you-do. Every beat has its own visual; the host's words run as captions.
type Item = {emoji: string; label?: string};
export type Visual =
	| {kind: 'hook'; emoji: string; text: string; options?: Item[]} // options: the choice's, shown from the first frame
	| {kind: 'emoji'; emoji: string; label?: string; motion?: 'bounce' | 'spin' | 'zoom' | 'shake' | 'float'}
	| {kind: 'pair'; a: Item; b: Item; vs?: boolean}
	| {kind: 'steps'; items: Item[]}
	| {kind: 'number'; value: number; unit: string; emoji?: string}
	| {kind: 'choice'; question: string; options: Item[]; answer: number; timerAt: number; timerLen: number; revealAt: number}
	| {kind: 'fact'; emoji: string; text: string}
	| {kind: 'scale'; items: (Item & {size: number})[]}
	| {kind: 'clues'; items: Item[]}
	| {kind: 'suspects'; items: Item[]; pick?: number | null; revealAt?: number | null};
type Chunk = {words: string[]; hl: boolean[]; at: number; until: number};
export type LookProps = {
	bg: 'blobs' | 'grid' | 'spotlight' | 'stripes' | 'dots' | 'stars' | 'chalk' | 'paper';
	head: string;
	caption: string;
	card: 'round' | 'sticker' | 'square';
	move: 'rise' | 'slide' | 'zoom';
	seed: number;
};
const DEFAULT_LOOK: LookProps = {bg: 'blobs', head: 'lilita', caption: 'anton', card: 'round', move: 'rise', seed: 0};
const LookCtx = createContext<LookProps>(DEFAULT_LOOK);
const useLook = () => {
	const l = useContext(LookCtx);
	return {...l, headFont: FONTS[l.head] ?? display, captionFont: FONTS[l.caption] ?? anton};
};
/** How a card sits: rounded, a tilted sticker with a white rim, or square-cornered. */
const card = (l: LookProps, i: number, radius = 36): React.CSSProperties =>
	l.card === 'sticker'
		? {borderRadius: radius * 0.6, transform: `rotate(${(i % 2 ? 1 : -1) * (1.5 + ((l.seed + i) % 3) * 0.6)}deg)`, outline: '6px solid rgba(255,255,255,0.9)'}
		: l.card === 'square'
			? {borderRadius: 10}
			: {borderRadius: radius};
export type SnackBeat = {from: number; duration: number; visual: Visual};
export type SnackProps = {
	durationInFrames: number;
	audio: string;
	format: 'why' | 'how' | 'mystery' | 'myth' | 'real' | 'whatif' | 'teaser' | 'origin';
	look?: LookProps;
	title: string;
	theme: {a: string; b: string; accent: string};
	beats: SnackBeat[];
	chunks: Chunk[];
	endAt: number;
};

const INK = '#1f1b3a';
const GREEN = '#22C55E';
const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const hash = (n: number) => {
	const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
	return x - Math.floor(x);
};
const TAGS: Record<string, string> = {
	why: 'WHY?',
	how: 'HOW IT WORKS',
	mystery: 'MYSTERY',
	myth: 'MYTH OR FACT?',
	real: 'REAL LIFE',
	whatif: 'WHAT IF?',
	teaser: 'BRAIN TEASER',
	origin: 'THE STORY BEHIND',
};

const Emoji: React.FC<{e: string; size: number; style?: React.CSSProperties}> = ({e, size, style}) => (
	<span style={{fontFamily: EMOJI, fontSize: size, lineHeight: 1, filter: 'drop-shadow(0 14px 0 rgba(0,0,0,0.18))', ...style}}>{e}</span>
);

const Label: React.FC<{text?: string; size?: number; color?: string; gap?: number}> = ({text, size = 54, color = '#ffffff', gap = 16}) => {
	const l = useLook();
	return text ? <div style={{fontFamily: l.headFont, fontSize: size, color, textAlign: 'center', lineHeight: 1.05, textShadow: '0 6px 0 rgba(0,0,0,0.22)', marginTop: gap}}>{text}</div> : null;
};

/** Springs a child in at frame `at` (relative to the beat). */
const In: React.FC<{at: number; children: React.ReactNode; style?: React.CSSProperties}> = ({at, children, style}) => {
	const f = useCurrentFrame();
	const {fps} = useVideoConfig();
	const s = spring({frame: f - at, fps, config: {damping: 11, stiffness: 150}});
	return <div style={{transform: `scale(${s})`, opacity: clamp(s * 2), ...style}}>{children}</div>;
};

// ---------------------------------------------------------------- the visuals
const VisualView: React.FC<{v: Visual; duration: number; theme: SnackProps['theme']}> = ({v, duration, theme}) => {
	const f = useCurrentFrame();
	const {fps} = useVideoConfig();
	const l = useLook();
	const stagger = (n: number, i: number) => Math.round((i * Math.min(duration * 0.55, n * 24)) / Math.max(1, n));
	const center: React.CSSProperties = {position: 'absolute', left: 60, right: 60, top: 300, height: 860, display: 'flex', alignItems: 'center', justifyContent: 'center'};
	switch (v.kind) {
		case 'hook':
			if (v.options?.length) {
				// the first second: the question and its answers are already there, so the viewer starts guessing at once
				return (
					<div style={{position: 'absolute', left: 70, right: 70, top: 280, height: 900, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 34}}>
						<div style={{display: 'flex', alignItems: 'center', gap: 26}}>
							<Emoji e={v.emoji} size={170} style={{display: 'inline-block', transform: `rotate(${Math.sin(f / 9) * 6}deg)`}} />
							<div style={{fontFamily: l.headFont, fontSize: 54, color: INK, background: theme.accent, padding: '8px 26px', borderRadius: 34, transform: `rotate(-3deg) scale(${1 + 0.05 * Math.sin(f / 5)})`, boxShadow: '0 8px 0 rgba(0,0,0,0.2)', whiteSpace: 'nowrap'}}>⏸ PAUSE &amp; GUESS</div>
						</div>
						<div style={{fontFamily: l.headFont, fontSize: v.text.length > 26 ? 86 : 100, color: '#fff', textAlign: 'center', lineHeight: 1.05, textShadow: '0 8px 0 rgba(0,0,0,0.25)'}}>{v.text}</div>
						<div style={{display: 'flex', gap: 22, justifyContent: 'center', flexWrap: 'wrap'}}>
							{v.options.map((o, i) => (
								<div key={i} style={{width: v.options!.length > 3 ? 205 : 255, padding: '20px 10px', ...card(l, i), background: '#ffffff', display: 'flex', flexDirection: 'column', alignItems: 'center', boxShadow: '0 12px 0 rgba(0,0,0,0.18)', transform: `translateY(${Math.sin(f / 10 + i) * 6}px)`}}>
									<Emoji e={o.emoji} size={100} />
									<div style={{fontFamily: body, fontWeight: 900, fontSize: 40, color: INK, marginTop: 8, textAlign: 'center', lineHeight: 1.1}}>{o.label}</div>
								</div>
							))}
						</div>
					</div>
				);
			}
			return (
				<div style={{...center, flexDirection: 'column'}}>
					<In at={0}>
						<Emoji e={v.emoji} size={380} style={{display: 'inline-block', transform: `rotate(${Math.sin(f / 9) * 6}deg)`}} />
					</In>
					<In at={8}>
						<div style={{fontFamily: l.headFont, fontSize: v.text.length > 26 ? 88 : 104, color: '#fff', textAlign: 'center', lineHeight: 1.05, marginTop: 40, textShadow: '0 8px 0 rgba(0,0,0,0.25)'}}>{v.text}</div>
					</In>
				</div>
			);
		case 'emoji': {
			const m = v.motion ?? 'bounce';
			const t =
				m === 'spin' ? `rotate(${f * 4}deg)` : m === 'zoom' ? `scale(${1 + 0.12 * Math.sin(f / 7)})` : m === 'shake' ? `translateX(${Math.sin(f * 1.3) * 14}px)` : m === 'float' ? `translateY(${Math.sin(f / 14) * 26}px)` : `translateY(${-Math.abs(Math.sin(f / 8)) * 50}px)`;
			return (
				<div style={{...center, flexDirection: 'column'}}>
					<In at={0}>
						<Emoji e={v.emoji} size={460} style={{display: 'inline-block', transform: t}} />
					</In>
					<In at={10}>
						<Label text={v.label} size={80} gap={44} />
					</In>
				</div>
			);
		}
		case 'pair':
			return (
				<div style={{...center, gap: 30}}>
					{[v.a, v.b].map((it, i) => (
						<React.Fragment key={i}>
							{i === 1 && v.vs !== false ? (
								<In at={10}>
									<div style={{fontFamily: l.headFont, fontSize: 90, color: theme.accent, textShadow: '0 6px 0 rgba(0,0,0,0.25)'}}>VS</div>
								</In>
							) : null}
							<In at={i * 16} style={{display: 'flex', flexDirection: 'column', alignItems: 'center', width: 400}}>
								<Emoji e={it.emoji} size={240} style={{display: 'inline-block', transform: `translateY(${Math.sin(f / 10 + i * 2) * 12}px)`}} />
								<Label text={it.label} size={56} />
							</In>
						</React.Fragment>
					))}
				</div>
			);
		case 'steps':
			return (
				<div style={{...center, flexDirection: 'column', gap: 10}}>
					{v.items.map((it, i) => (
						<React.Fragment key={i}>
							{i > 0 ? (
								<In at={stagger(v.items.length, i) - 4}>
									<div style={{fontSize: 70, color: theme.accent, fontFamily: l.headFont, lineHeight: 1}}>↓</div>
								</In>
							) : null}
							<In at={stagger(v.items.length, i)} style={{display: 'flex', alignItems: 'center', gap: 30, background: 'rgba(255,255,255,0.14)', padding: '16px 34px', width: 860, ...card(l, i, 40)}}>
								<Emoji e={it.emoji} size={v.items.length > 3 ? 110 : 140} />
								<div style={{fontFamily: l.headFont, fontSize: v.items.length > 3 ? 54 : 64, color: '#fff', textShadow: '0 5px 0 rgba(0,0,0,0.2)', lineHeight: 1.05}}>{it.label}</div>
							</In>
						</React.Fragment>
					))}
				</div>
			);
		case 'number': {
			const p = clamp(f / Math.min(45, duration * 0.6));
			const eased = 1 - Math.pow(1 - p, 3);
			const shown = v.value >= 100 ? Math.round(v.value * eased).toLocaleString('en-US') : (v.value * eased).toFixed(Number.isInteger(v.value) ? 0 : 1);
			return (
				<div style={{...center, flexDirection: 'column'}}>
					{v.emoji ? (
						<In at={0}>
							<Emoji e={v.emoji} size={220} />
						</In>
					) : null}
					<div style={{fontFamily: anton, fontSize: shown.length > 7 ? 190 : 260, color: theme.accent, lineHeight: 1, textShadow: '0 12px 0 rgba(0,0,0,0.25)', marginTop: 20}}>{shown}</div>
					<In at={20}>
						<Label text={v.unit} size={74} />
					</In>
				</div>
			);
		}
		case 'choice': {
			const revealed = f >= v.revealAt;
			const left = clamp(1 - (f - v.timerAt) / v.timerLen);
			const secs = Math.max(1, Math.ceil(left * (v.timerLen / fps) - 0.001));
			return (
				<div style={{position: 'absolute', left: 80, right: 80, top: 300, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 26}}>
					<In at={0}>
						<div style={{fontFamily: body, fontWeight: 900, fontSize: v.question.length > 34 ? 60 : 70, color: INK, background: '#fff', padding: '26px 40px', textAlign: 'center', lineHeight: 1.15, boxShadow: '0 14px 0 rgba(0,0,0,0.18)', ...card(l, 1, 44)}}>{v.question}</div>
					</In>
					<div style={{display: 'flex', gap: 24, justifyContent: 'center', flexWrap: 'wrap', marginTop: 20}}>
						{v.options.map((o, i) => {
							const right = i === v.answer;
							const pulse = revealed && right ? 1 + 0.08 * Math.exp(-(f - v.revealAt) / 6) : 1;
							return (
								<In key={i} at={8 + i * 5}>
									<div style={{width: v.options.length > 3 ? 210 : 260, padding: '24px 10px', ...card(l, i), background: revealed && right ? GREEN : '#ffffff', opacity: revealed && !right ? 0.4 : 1, scale: String(pulse), display: 'flex', flexDirection: 'column', alignItems: 'center', boxShadow: '0 12px 0 rgba(0,0,0,0.18)'}}>
										<Emoji e={o.emoji} size={110} />
										<div style={{fontFamily: body, fontWeight: 900, fontSize: 42, color: revealed && right ? '#fff' : INK, marginTop: 10, textAlign: 'center', lineHeight: 1.1}}>{o.label}</div>
									</div>
								</In>
							);
						})}
					</div>
					{f >= v.timerAt && !revealed ? (
						<div style={{marginTop: 30, width: 170, height: 170, borderRadius: 85, background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: `0 0 0 14px ${left < 0.34 ? '#EF4444' : theme.accent}`}}>
							<span style={{fontFamily: l.headFont, fontSize: 96, color: INK}}>{secs}</span>
						</div>
					) : null}
				</div>
			);
		}
		case 'fact':
			return (
				<div style={{...center, flexDirection: 'column'}}>
					<In at={0}>
						<div style={{fontFamily: l.headFont, fontSize: 64, color: INK, background: theme.accent, padding: '10px 34px', borderRadius: 40, transform: 'rotate(-3deg)', boxShadow: '0 8px 0 rgba(0,0,0,0.2)'}}>BONUS FACT</div>
					</In>
					<In at={6}>
						<Emoji e={v.emoji} size={300} style={{display: 'inline-block', marginTop: 30, transform: `rotate(${Math.sin(f / 12) * 6}deg)`}} />
					</In>
					<In at={14}>
						<div style={{fontFamily: body, fontWeight: 900, fontSize: v.text.length > 60 ? 54 : 64, color: '#fff', textAlign: 'center', lineHeight: 1.18, marginTop: 30, textShadow: '0 5px 0 rgba(0,0,0,0.2)'}}>{v.text}</div>
					</In>
				</div>
			);
		case 'scale': {
			const max = Math.max(...v.items.map((i) => i.size));
			return (
				<div style={{...center, alignItems: 'flex-end', gap: 40, paddingBottom: 120}}>
					{v.items.map((it, i) => (
						<In key={i} at={stagger(v.items.length, i)} style={{display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
							<Emoji e={it.emoji} size={70 + 330 * (it.size / max)} />
							<Label text={it.label} size={48} />
						</In>
					))}
				</div>
			);
		}
		case 'clues':
			return (
				<div style={{...center, flexDirection: 'column', gap: 22}}>
					<In at={0}>
						<div style={{fontFamily: l.headFont, fontSize: 60, color: INK, background: theme.accent, padding: '8px 30px', borderRadius: 36}}>CLUES</div>
					</In>
					{v.items.map((it, i) => (
						<In key={i} at={stagger(v.items.length, i) + 6} style={{display: 'flex', alignItems: 'center', gap: 26, background: '#fff', padding: '16px 30px', width: 860, boxShadow: '0 10px 0 rgba(0,0,0,0.16)', ...card(l, i, 34)}}>
							<div style={{fontFamily: l.headFont, fontSize: 56, color: theme.a, width: 50}}>{i + 1}</div>
							<Emoji e={it.emoji} size={96} />
							<div style={{fontFamily: body, fontWeight: 900, fontSize: 44, color: INK, lineHeight: 1.15}}>{it.label}</div>
						</In>
					))}
				</div>
			);
		case 'suspects': {
			const revealed = v.revealAt != null && f >= v.revealAt;
			return (
				<div style={{...center, flexWrap: 'wrap', gap: 30}}>
					{v.items.map((it, i) => {
						const picked = revealed && i === v.pick;
						return (
							<In key={i} at={i * 8} style={{display: 'flex', flexDirection: 'column', alignItems: 'center', width: 280, padding: 20, ...card(l, i, 40), background: picked ? '#fff' : 'rgba(255,255,255,0.14)', opacity: revealed && !picked ? 0.35 : 1, scale: picked ? String(1.08 + 0.04 * Math.sin(f / 5)) : undefined, boxShadow: picked ? `0 0 0 12px ${theme.accent}` : undefined}}>
								<Emoji e={it.emoji} size={170} />
								<div style={{fontFamily: l.headFont, fontSize: 48, color: picked ? INK : '#fff', marginTop: 10, textAlign: 'center'}}>{it.label}</div>
							</In>
						);
					})}
				</div>
			);
		}
	}
};

// ---------------------------------------------------------------- frame pieces
/** The moving background. Each format has its own kind (scripts/snack.py LOOKS); `shift` changes with every beat. */
const Backdrop: React.FC<{theme: SnackProps['theme']; shift: number}> = ({theme, shift}) => {
	const f = useCurrentFrame();
	const l = useLook();
	const base = `linear-gradient(${160 + shift * 25}deg, ${theme.a} 0%, ${theme.b} 100%)`;
	const seed = l.seed;
	const glow = (n: number, alpha: number) =>
		Array.from({length: n}, (_, i) => {
			const x = hash(i + shift + seed) * 1080 + Math.sin(f / (80 + i * 13) + i) * 70;
			const y = hash(i + 9 + shift + seed) * 1920 + Math.cos(f / (100 + i * 11) + i) * 80;
			const r = 200 + hash(i + 3 + seed) * 260;
			return <div key={i} style={{position: 'absolute', left: x - r, top: y - r, width: r * 2, height: r * 2, borderRadius: '50%', background: `radial-gradient(circle, rgba(255,255,255,${alpha}) 0%, rgba(255,255,255,0) 70%)`}} />;
		});
	const fill: React.CSSProperties = {position: 'absolute', inset: 0};
	switch (l.bg) {
		case 'grid': // a blueprint: fine and bold lines drifting slowly
			return (
				<AbsoluteFill style={{background: base, overflow: 'hidden'}}>
					<div style={{...fill, inset: -200, transform: `translate(${(f * 0.6) % 120}px, ${(f * 0.4) % 120}px)`, backgroundImage: 'linear-gradient(rgba(255,255,255,0.16) 3px, transparent 3px), linear-gradient(90deg, rgba(255,255,255,0.16) 3px, transparent 3px), linear-gradient(rgba(255,255,255,0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.07) 1px, transparent 1px)', backgroundSize: '120px 120px, 120px 120px, 24px 24px, 24px 24px'}} />
					{glow(3, 0.1)}
				</AbsoluteFill>
			);
		case 'spotlight': { // dark room, a searchlight sweeping
			const x = 540 + Math.sin(f / 50 + seed) * 300;
			const y = 760 + Math.cos(f / 70 + seed) * 260;
			return (
				<AbsoluteFill style={{background: theme.a, overflow: 'hidden'}}>
					<div style={{...fill, background: `radial-gradient(circle 620px at ${x}px ${y}px, ${theme.b} 0%, rgba(0,0,0,0) 100%)`, opacity: 0.95}} />
					<div style={{...fill, background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 45%, rgba(0,0,0,0.6) 100%)'}} />
					<div style={{...fill, backgroundImage: 'repeating-linear-gradient(0deg, rgba(255,255,255,0.025) 0 2px, transparent 2px 6px)'}} />
				</AbsoluteFill>
			);
		}
		case 'stripes': // bold diagonal stripes sliding
			return (
				<AbsoluteFill style={{background: base, overflow: 'hidden'}}>
					<div style={{...fill, inset: -300, transform: `translateX(${(f * 1.2) % 160}px) rotate(${-20 + (seed % 3) * 20}deg)`, backgroundImage: 'repeating-linear-gradient(90deg, rgba(255,255,255,0.09) 0 80px, transparent 80px 160px)'}} />
					{glow(3, 0.12)}
				</AbsoluteFill>
			);
		case 'dots': // halftone dots, gently pulsing
			return (
				<AbsoluteFill style={{background: base, overflow: 'hidden'}}>
					<div style={{...fill, inset: -100, transform: `translateY(${(f * 0.5) % 56}px)`, backgroundImage: `radial-gradient(circle, rgba(255,255,255,${0.13 + 0.04 * Math.sin(f / 20)}) 7px, transparent 8px)`, backgroundSize: '56px 56px'}} />
					<div style={{...fill, background: 'radial-gradient(ellipse at 50% 40%, rgba(255,255,255,0.12) 0%, rgba(0,0,0,0.18) 100%)'}} />
				</AbsoluteFill>
			);
		case 'stars': // night sky: twinkling stars, a slow nebula
			return (
				<AbsoluteFill style={{background: `radial-gradient(ellipse at ${30 + (seed % 40)}% 30%, ${theme.b} 0%, ${theme.a} 70%)`, overflow: 'hidden'}}>
					{Array.from({length: 90}, (_, i) => {
						const tw = 0.35 + 0.65 * Math.abs(Math.sin(f / (12 + (i % 7) * 3) + i));
						const r = 2 + hash(i * 7 + seed) * 4;
						return <div key={i} style={{position: 'absolute', left: hash(i + seed) * 1080, top: (hash(i * 3 + 1 + seed) * 1920 + f * (0.2 + r * 0.05)) % 1920, width: r, height: r, borderRadius: '50%', background: '#fff', opacity: tw}} />;
					})}
				</AbsoluteFill>
			);
		case 'chalk': // a chalkboard with smudges and a wooden frame
			return (
				<AbsoluteFill style={{background: `linear-gradient(170deg, ${theme.a}, ${theme.b})`, overflow: 'hidden'}}>
					{Array.from({length: 9}, (_, i) => (
						<div key={i} style={{position: 'absolute', left: hash(i + seed) * 1000 - 150, top: hash(i + 5 + seed) * 1800, width: 420, height: 140, borderRadius: '50%', background: 'rgba(255,255,255,0.05)', filter: 'blur(30px)', transform: `rotate(${hash(i + 2) * 60 - 30}deg)`}} />
					))}
					<div style={{...fill, boxShadow: 'inset 0 0 0 26px #7c4a24, inset 0 0 0 34px #5b3418, inset 0 0 80px 40px rgba(0,0,0,0.45)'}} />
				</AbsoluteFill>
			);
		case 'paper': // old paper: warm, ruled, a soft vignette
			return (
				<AbsoluteFill style={{background: base, overflow: 'hidden'}}>
					<div style={{...fill, backgroundImage: 'repeating-linear-gradient(0deg, rgba(255,240,200,0.07) 0 2px, transparent 2px 64px)', transform: `translateY(${(f * 0.3) % 64}px)`}} />
					<div style={{...fill, background: 'radial-gradient(ellipse at center, rgba(255,230,180,0.14) 0%, rgba(0,0,0,0.45) 100%)'}} />
				</AbsoluteFill>
			);
		default: // 'blobs': soft light blobs drifting
			return (
				<AbsoluteFill style={{background: base, overflow: 'hidden'}}>
					{glow(7, 0.15)}
				</AbsoluteFill>
			);
	}
};

const Brand: React.FC<{format: string; accent: string}> = ({format, accent}) => (
	<div style={{position: 'absolute', top: 92, width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 18}}>
		<div style={{display: 'flex', alignItems: 'center', gap: 12, padding: '6px 26px 6px 12px', borderRadius: 50, background: 'rgba(255,255,255,0.16)', border: '3px solid rgba(255,255,255,0.35)'}}>
			<BrainLogo size={56} />
			<span style={{fontFamily: display, fontSize: 38, color: '#fff'}}>BRAIN SNACK</span>
		</div>
		<span style={{fontFamily: display, fontSize: 38, color: INK, background: accent, padding: '8px 22px', borderRadius: 40}}>{TAGS[format]}</span>
	</div>
);

const Captions: React.FC<{chunks: Chunk[]; accent: string; endAt: number}> = ({chunks, accent, endAt}) => {
	const f = useCurrentFrame();
	const l = useLook();
	const size = l.caption === 'bebas' || l.caption === 'oswald' ? 104 : l.caption === 'marker' || l.caption === 'bangers' ? 92 : 96;
	const {fps} = useVideoConfig();
	const c = chunks.find((k) => f >= k.at && f < k.until);
	if (!c) return null;
	const pop = spring({frame: f - c.at, fps, config: {damping: 14, stiffness: 260}});
	return (
		<div style={{position: 'absolute', left: 60, right: 60, top: f >= endAt ? 1480 : 1240, display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: '0 22px', transform: `scale(${0.86 + 0.14 * pop})`}}>
			{c.words.map((w, i) => (
				<span key={i} style={{fontFamily: l.captionFont, fontSize: size, lineHeight: 1.12, textTransform: 'uppercase', color: c.hl[i] ? accent : '#ffffff', WebkitTextStroke: '12px #1f1b3a', paintOrder: 'stroke fill'}}>
					{w}
				</span>
			))}
		</div>
	);
};

const ASK: Record<SnackProps['format'], string> = {
	why: 'WHAT SHOULD WE EXPLAIN NEXT? 👇',
	how: 'WHAT SHOULD WE TAKE APART NEXT? 👇',
	mystery: 'DID YOU SOLVE IT? TELL US 👇',
	myth: 'WHICH MYTH SHOULD WE TEST NEXT? 👇',
	whatif: 'WHAT IF... WHAT? TELL US 👇',
	teaser: 'GOT IT? TELL US HOW FAST 👇',
	origin: 'WHAT SHOULD WE LOOK INTO NEXT? 👇',
	real: 'WHAT WOULD YOU DO? 👇',
};

const EndCard: React.FC<{endAt: number; theme: SnackProps['theme']; format: SnackProps['format']}> = ({endAt, theme, format}) => {
	const f = useCurrentFrame() - endAt;
	const {fps} = useVideoConfig();
	if (f < 0) return null;
	return (
		<AbsoluteFill style={{background: `linear-gradient(rgba(31,27,58,0.45), rgba(31,27,58,0.45)), linear-gradient(170deg, ${theme.a}, ${theme.b})`, opacity: clamp(f / 10), display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 30, paddingBottom: 260}}>
			<div style={{transform: `scale(${spring({frame: f, fps, config: {damping: 10}})})`}}>
				<BrainLogo size={260} />
			</div>
			<div style={{fontFamily: display, fontSize: 92, color: '#fff', textAlign: 'center', lineHeight: 1.05, opacity: clamp((f - 6) / 8)}}>
				NEW SNACK
				<br />
				EVERY DAY
			</div>
			<div style={{fontFamily: display, fontSize: 56, color: INK, background: theme.accent, padding: '12px 30px', borderRadius: 40, opacity: clamp((f - 14) / 8), maxWidth: 900, textAlign: 'center'}}>{ASK[format]}</div>
		</AbsoluteFill>
	);
};

// ---------------------------------------------------------------- composition
export const Snack: React.FC<SnackProps> = ({beats, chunks, audio, format, theme, endAt, look = DEFAULT_LOOK}) => {
	const f = useCurrentFrame();
	const current = beats.findIndex((b) => f >= b.from && f < b.from + b.duration);
	return (
		<LookCtx.Provider value={look}>
		<AbsoluteFill>
			<Backdrop theme={theme} shift={Math.max(0, current) % 4} />
			{beats.map((b, i) => (
				<Sequence key={i} from={b.from} durationInFrames={b.duration}>
					<BeatView b={b} theme={theme} />
				</Sequence>
			))}
			<Brand format={format} accent={theme.accent} />
			<EndCard endAt={endAt} theme={theme} format={format} />
			<Captions chunks={chunks} accent={theme.accent} endAt={endAt} />
			{audio ? <Audio src={staticFile(audio)} /> : null}
		</AbsoluteFill>
		</LookCtx.Provider>
	);
};

const BeatView: React.FC<{b: SnackBeat; theme: SnackProps['theme']}> = ({b, theme}) => {
	const f = useCurrentFrame();
	const l = useLook();
	const out = clamp((f - (b.duration - 6)) / 6);
	const t = l.move === 'slide' ? `translateX(${-out * 160}px)` : l.move === 'zoom' ? `scale(${1 + out * 0.15})` : `translateY(${-out * 40}px)`;
	return (
		<AbsoluteFill style={{opacity: 1 - out, transform: t}}>
			<VisualView v={b.visual} duration={b.duration} theme={theme} />
		</AbsoluteFill>
	);
};

