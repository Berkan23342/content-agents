import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Look, PopWord, RAINBOW, Season, blinkAt, textStyle} from './common';
import {Bg, Confetti, Rays, Scenery, Shards} from './Fun';
import {EggView, Hero, HeroView, Pop, SpeechBubble} from './hero';

// ---------------------------------------------------------------- props (written by scripts/short.py)
// A vertical 1080x1920 YouTube Short: three quick rounds of one game, then a goodbye.
// Everything important stays inside x 60-940, y 120-1450: YouTube draws its buttons and the title over the rest.
type Timed = {text: string; color: string; at: number};

export type ShortScene =
	| {type: 'shadow'; from: number; duration: number; hero: Hero; counts: number[]; revealAt: number; name: Timed; bubble?: Timed | null}
	| {type: 'egg'; from: number; duration: number; egg: Hero; ticks: number[]; openAt: number; hero: Hero; name: Timed; bubble?: Timed | null}
	| {type: 'count'; from: number; duration: number; item: Hero; n: number; counts: number[]; answer: Timed}
	| {type: 'end'; from: number; duration: number; heroes: Hero[]; text: string; byeAt: number};

export type ShortProps = {
	durationInFrames: number;
	audio: string;
	bg: Bg;
	header: string;
	scenes: ShortScene[];
	season?: Season;
	look?: number;
};

const CX = 540;
const HERO_Y = 1010;
const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));

/** The landscape scenery, zoomed to cover the tall frame (it is all vector art, so it stays sharp). */
const Backdrop: React.FC<{bg: Bg}> = ({bg}) => {
	const k = 1920 / 1080;
	return (
		<div style={{position: 'absolute', left: (1080 - 1920 * k) / 2, top: 0, width: 1920, height: 1080, transform: `scale(${k})`, transformOrigin: '0 0'}}>
			<Scenery bg={bg} tint={null} />
		</div>
	);
};

/** Game name and one dot per round, at the top. */
const Header: React.FC<{text: string; round: number; rounds: number}> = ({text, round, rounds}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const s = spring({frame, fps, config: {damping: 12}});
	return (
		<div style={{position: 'absolute', top: 128, width: '100%', display: 'flex', justifyContent: 'center', transform: `scale(${s})`}}>
			<div style={{background: '#ffffff', borderRadius: 60, padding: '14px 34px', display: 'flex', alignItems: 'center', gap: 22, boxShadow: '0 8px 0 rgba(0,0,0,0.12)'}}>
				<span style={{...textStyle('#2F8CFF', 50), WebkitTextStroke: '0px', filter: 'none'}}>{text}</span>
				{Array.from({length: rounds}, (_, i) => (
					<div
						key={i}
						style={{width: 26, height: 26, borderRadius: 13, background: i < round ? RAINBOW[(i * 2) % 7] : '#dfe6ef', transform: `scale(${i === round - 1 ? 1.25 : 1})`}}
					/>
				))}
			</div>
		</div>
	);
};

/** Big headline under the header: the question first, then the answer. */
const Headline: React.FC<{question: string; answer: Timed; gone: number}> = ({question, answer, gone}) => {
	const frame = useCurrentFrame();
	const fit = (s: string, max: number) => Math.min(max, Math.round(1500 / Math.max(1, s.length)));
	return (
		<div style={{position: 'absolute', top: 262, width: '100%', opacity: 1 - gone}}>
			{frame < answer.at ? (
				<PopWord text={question} color={RAINBOW} size={fit(question, 140)} startFrame={4} />
			) : (
				<PopWord text={answer.text} color={answer.color} size={fit(answer.text, 170)} startFrame={answer.at} />
			)}
		</div>
	);
};

/** A countdown digit that pops over the middle of the screen. */
const Digit: React.FC<{value: string; at: number; color: string}> = ({value, at, color}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const d = frame - at;
	if (d < 0 || d > 24) return null;
	const s = spring({frame: d, fps, config: {damping: 8}});
	return (
		<div style={{position: 'absolute', top: HERO_Y - 190, width: '100%', textAlign: 'center', opacity: clamp((24 - d) / 7), transform: `scale(${s})`}}>
			<span style={textStyle(color, 380)}>{value}</span>
		</div>
	);
};

const Bubble: React.FC<{bubble?: Timed | null; gone: number}> = ({bubble, gone}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	if (!bubble || frame < bubble.at) return null;
	const s = spring({frame: frame - bubble.at, fps, config: {damping: 10}}) * (1 - gone);
	return <SpeechBubble text={bubble.text} color={bubble.color} x={CX + 120} y={HERO_Y - 330} size={84} scale={s} />;
};

// ---------------------------------------------------------------- rounds
const ShadowRound: React.FC<{scene: Extract<ShortScene, {type: 'shadow'}>}> = ({scene}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const enter = spring({frame, fps, config: {damping: 10, stiffness: 120}});
	const light = clamp((frame - scene.revealAt) / 10);
	const bounce = frame >= scene.revealAt ? 1 + 0.22 * Math.exp(-(frame - scene.revealAt) / 8) : 1;
	const gone = clamp((frame - (scene.duration - 12)) / 10);
	const bob = Math.sin(frame / 12) * 12;
	return (
		<AbsoluteFill>
			{light > 0 ? <Rays x={CX} y={HERO_Y} r={760} color="#fff6b0" opacity={light * (1 - gone) * 0.8} frame={frame} /> : null}
			<Headline question="Who am I?" answer={scene.name} gone={gone} />
			<div
				style={{
					position: 'absolute',
					inset: 0,
					transform: `translateY(${bob}px) scale(${enter * bounce * (1 - gone)})`,
					transformOrigin: `${CX}px ${HERO_Y}px`,
					filter: light < 1 ? `brightness(${light})` : undefined,
				}}
			>
				<HeroView hero={scene.hero} x={CX} y={HERO_Y} size={620} blink={light < 1 ? 1 : blinkAt(frame, scene.from)} />
			</div>
			{frame < scene.revealAt
				? [
						[150, 700],
						[905, 650],
						[170, 1330],
					].map(([x, y], i) => (
						<div key={i} style={{position: 'absolute', left: x - 60, top: y - 90 + Math.sin((frame + i * 20) / 10) * 18, opacity: enter}}>
							<span style={textStyle(RAINBOW[(i * 2) % 7], 170)}>?</span>
						</div>
					))
				: null}
			{scene.counts.map((t, i) => (
				<Digit key={i} value={String(3 - i)} at={t} color={RAINBOW[i * 2]} />
			))}
			<Confetti x={CX} y={HERO_Y - 40} at={scene.revealAt} count={46} />
			<Bubble bubble={scene.bubble} gone={gone} />
		</AbsoluteFill>
	);
};

const EggRound: React.FC<{scene: Extract<ShortScene, {type: 'egg'}>}> = ({scene}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const drop = spring({frame, fps, config: {damping: 9, stiffness: 90}});
	let rot = 0;
	let cracked = 0;
	scene.ticks.forEach((t, i) => {
		if (frame >= t) {
			rot += Math.sin((frame - t) * 0.9) * 14 * Math.exp(-(frame - t) / 10);
			cracked = (i + clamp((frame - t) / 6)) / scene.ticks.length;
		}
	});
	const open = clamp((frame - scene.openAt) / 18);
	const rise = spring({frame: frame - scene.openAt, fps, config: {damping: 8, stiffness: 110}});
	const gone = clamp((frame - (scene.duration - 12)) / 10);
	const size = 660;
	const eggY = interpolate(drop, [0, 1], [-700, HERO_Y]);
	return (
		<AbsoluteFill>
			{frame >= scene.openAt ? <Rays x={CX} y={HERO_Y} r={760} color="#fff6b0" opacity={rise * (1 - gone) * 0.8} frame={frame} /> : null}
			<Headline question="What's inside?" answer={scene.name} gone={gone} />
			{open < 1 || frame < scene.openAt + 30 ? (
				<div style={{position: 'absolute', inset: 0, transform: `rotate(${rot}deg)`, transformOrigin: `${CX}px ${eggY + size / 2}px`, opacity: 1 - gone}}>
					<div style={{position: 'absolute', left: CX - (size * 0.77) / 2, top: eggY - size / 2}}>
						<EggView value={scene.egg.value} color={scene.egg.color} size={size} crack={cracked} open={open} id={`s${scene.from}`} />
					</div>
				</div>
			) : null}
			<Shards x={CX} y={HERO_Y - 40} at={scene.openAt} color={scene.egg.color} />
			{frame >= scene.openAt ? (
				<div style={{position: 'absolute', inset: 0, transform: `scale(${rise * (1 - gone)})`, transformOrigin: `${CX}px ${HERO_Y + 60}px`}}>
					<HeroView hero={scene.hero} x={CX} y={interpolate(rise, [0, 1], [HERO_Y + 160, HERO_Y])} size={560} blink={blinkAt(frame, scene.from)} />
				</div>
			) : null}
			<Confetti x={CX} y={HERO_Y - 40} at={scene.openAt} count={50} />
			<Bubble bubble={scene.bubble} gone={gone} />
		</AbsoluteFill>
	);
};

/** n items in a grid; each one bounces and gets its number when it is counted. */
const CountRound: React.FC<{scene: Extract<ShortScene, {type: 'count'}>}> = ({scene}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const {n} = scene;
	const cols = n <= 4 ? 2 : 3;
	const rows = Math.ceil(n / cols);
	const gap = n <= 4 ? 330 : 290;
	const size = n <= 4 ? 260 : 220;
	const gone = clamp((frame - (scene.duration - 12)) / 10);
	const done = frame >= scene.answer.at;
	return (
		<AbsoluteFill>
			{done ? <Rays x={CX} y={HERO_Y} r={760} color="#fff6b0" opacity={clamp((frame - scene.answer.at) / 10) * (1 - gone) * 0.7} frame={frame} /> : null}
			<Headline question="How many?" answer={scene.answer} gone={gone} />
			{Array.from({length: n}, (_, i) => {
				const r = Math.floor(i / cols);
				const inRow = r === rows - 1 ? n - r * cols : cols;
				const c = i % cols;
				const x = CX + (c - (inRow - 1) / 2) * gap;
				const y = HERO_Y + (r - (rows - 1) / 2) * gap * 0.95;
				const t = scene.counts[i];
				const hit = frame >= t ? 1 + 0.35 * Math.exp(-(frame - t) / 8) : 1;
				const label = spring({frame: frame - t, fps, config: {damping: 10}});
				const party = done ? Math.sin((frame - scene.answer.at) / 4 + i) * 0.06 : 0;
				return (
					<div key={i}>
						<Pop at={4 + i * 3} seed={i} bob={6}>
							<div style={{position: 'absolute', inset: 0, transform: `scale(${(hit + party) * (1 - gone)})`, transformOrigin: `${x}px ${y}px`}}>
								<HeroView hero={scene.item} x={x} y={y} size={size} blink={blinkAt(frame, i)} />
							</div>
						</Pop>
						{frame >= t ? (
							<div style={{position: 'absolute', left: x - 70, top: y + size * 0.28, width: 140, textAlign: 'center', transform: `scale(${label * (1 - gone)})`, transformOrigin: '50% 30%'}}>
								<span style={textStyle(RAINBOW[i % 7], 110)}>{i + 1}</span>
							</div>
						) : null}
					</div>
				);
			})}
			<Confetti x={CX} y={HERO_Y - 200} at={scene.answer.at} count={50} />
		</AbsoluteFill>
	);
};

const End: React.FC<{scene: Extract<ShortScene, {type: 'end'}>}> = ({scene}) => {
	const frame = useCurrentFrame();
	const n = scene.heroes.length;
	return (
		<AbsoluteFill>
			<Rays x={CX} y={HERO_Y} r={760} color="#ffffff" opacity={0.3} frame={frame} count={16} />
			<div style={{position: 'absolute', top: 290, width: '100%'}}>
				<PopWord text={scene.text} color="#FF8A1F" size={Math.min(140, Math.round(1500 / scene.text.length))} startFrame={2} />
			</div>
			{scene.heroes.map((h, i) => (
				<Pop key={i} at={6 + i * 4} seed={i}>
					<HeroView hero={h} x={CX + (i - (n - 1) / 2) * 300} y={HERO_Y - 60} size={280} blink={blinkAt(frame, i)} />
				</Pop>
			))}
			<div style={{position: 'absolute', top: HERO_Y + 170, width: '100%'}}>
				<PopWord text="Bye bye!" color={RAINBOW} size={170} startFrame={scene.byeAt} />
			</div>
		</AbsoluteFill>
	);
};

// ---------------------------------------------------------------- composition
export const Short: React.FC<ShortProps> = ({scenes, audio, bg, header, season = 'spring', look = 0}) => {
	const frame = useCurrentFrame();
	const rounds = scenes.filter((s) => s.type !== 'end');
	const round = rounds.filter((s) => frame >= s.from).length;
	return (
		<Look.Provider value={{season, seed: look}}>
		<AbsoluteFill style={{background: '#8fd3ff'}}>
			<Backdrop bg={bg} />
			{scenes.map((s, i) => (
				<Sequence key={i} from={s.from} durationInFrames={s.duration}>
					{s.type === 'shadow' && <ShadowRound scene={s} />}
					{s.type === 'egg' && <EggRound scene={s} />}
					{s.type === 'count' && <CountRound scene={s} />}
					{s.type === 'end' && <End scene={s} />}
				</Sequence>
			))}
			<Header text={header} round={round} rounds={rounds.length} />
			{audio ? <Audio src={staticFile(audio)} /> : null}
		</AbsoluteFill>
		</Look.Provider>
	);
};
