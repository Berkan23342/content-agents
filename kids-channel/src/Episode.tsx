import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {FloatingBalloon, Look, PopWord, RAINBOW, Season, blinkAt, textStyle} from './common';
import {Bg, DanceScene, EggScene, FunScene, Rays, Scenery, ShadowScene, StoryScene, TitleCard, storyCam} from './Fun';
import {Hero, HeroView, Pop} from './hero';
import {mix} from './shapes';

// ---------------------------------------------------------------- props (written by scripts/episode.py and scripts/fun.py)
type Item = {kind: 'icon' | 'shape'; value: string; color: string; label?: string; at: number};
type Scene =
	| {type: 'intro'; from: number; duration: number; title: string[]; heroes: Hero[]}
	| {type: 'section'; from: number; duration: number; sub: string; text: string; heroes: Hero[]}
	| {
			type: 'focus';
			from: number;
			duration: number;
			layout: 'pair' | 'count' | 'trio' | 'animal' | 'letter';
			tint: string;
			title: {text: string; color: string; at: number};
			hero: Hero & {at: number};
			items: Item[];
			bubble?: {text: string; at: number} | null;
			caption?: {text: string; at: number} | null;
	  }
	| {type: 'review'; from: number; duration: number; heading: {text: string; color: string}; entries: {hero: Hero; label: string; at: number}[]}
	| {type: 'outro'; from: number; duration: number; byeAt: number; heroes: Hero[]; top?: string; bg?: Bg}
	| FunScene;

export type EpisodeProps = {
	durationInFrames: number;
	audio: string;
	scenes: Scene[];
	// badge: the story's kind ("A Kindness Story") in its colour; with a badge the thumbnail uses the story layout
	thumb: {title: string[]; heroes: Hero[]; bg?: Bg; badge?: string; badgeColor?: string; rays?: string};
	season?: Season; // from the video's date
	look?: number; // a seed: sky, sun and small details differ from video to video
};

// ---------------------------------------------------------------- building blocks
/** Positions a child so that its own transform origin is the anchor point. */
const At: React.FC<{x: number; y: number; children: React.ReactNode}> = ({x, y, children}) => (
	<div style={{position: 'absolute', left: x - 960, top: y - 540, width: 1920, height: 1080}}>{children}</div>
);

const Label: React.FC<{text: string; color: string; x: number; y: number; size?: number}> = ({text, color, x, y, size = 76}) => (
	<div style={{position: 'absolute', left: x - 400, top: y, width: 800, textAlign: 'center'}}>
		<span style={textStyle(mix(color, '#000000', 0.12), size)}>{text}</span>
	</div>
);

// ---------------------------------------------------------------- scenes
const Intro: React.FC<{duration: number; title: string[]}> = ({duration, title}) => {
	const positions = [
		[230, 380], [480, 520], [720, 600], [1200, 600], [1440, 520], [1690, 380], [960, 650],
	];
	return (
		<AbsoluteFill>
			{RAINBOW.map((c, i) => (
				<FloatingBalloon key={c} color={c} x={positions[i][0]} y={positions[i][1]} width={160} enterAt={4 + i * 4} seed={i} exitAt={duration - 22} />
			))}
			<div style={{position: 'absolute', top: 70, width: '100%'}}>
				<PopWord text="Bubbly Kids TV" color="#2F8CFF" size={70} startFrame={2} />
			</div>
			{title.map((line, i) => (
				<div key={line} style={{position: 'absolute', top: 190 + i * 160, width: '100%'}}>
					<PopWord text={line} color={RAINBOW} size={i === 0 ? 150 : 120} startFrame={12 + i * 18} />
				</div>
			))}
		</AbsoluteFill>
	);
};

const Section: React.FC<{duration: number; sub: string; text: string; heroes: Hero[]}> = ({duration, sub, text, heroes}) => {
	const frame = useCurrentFrame();
	const out = duration - 14;
	const n = heroes.length;
	return (
		<AbsoluteFill>
			<Pop at={0} outAt={out} bob={4}>
				<div style={{position: 'absolute', top: 170, width: '100%'}}>
					<PopWord text={sub} color="#2F8CFF" size={100} startFrame={2} />
				</div>
				<div style={{position: 'absolute', top: 310, width: '100%'}}>
					<PopWord text={text} color={RAINBOW} size={230} startFrame={10} />
				</div>
			</Pop>
			{heroes.map((h, i) => (
				<Pop key={i} at={18 + i * 5} outAt={out} seed={i}>
					<HeroView hero={h} x={960 + (i - (n - 1) / 2) * 260} y={760} size={190} blink={blinkAt(frame, i)} />
				</Pop>
			))}
		</AbsoluteFill>
	);
};

const Focus: React.FC<{scene: Extract<Scene, {type: 'focus'}>}> = ({scene}) => {
	const frame = useCurrentFrame();
	const {title, hero, items, layout, bubble, caption} = scene;
	const out = scene.duration - 16;
	const blink = blinkAt(frame, scene.from);

	const heroAt: Record<string, [number, number, number]> = {
		count: [380, 560, 400],
		trio: [960, 440, 400],
		animal: [860, 560, 500],
		letter: [560, 560, 430],
	};

	const itemPos = (i: number): [number, number, number] => {
		if (layout === 'pair') return [i === 0 ? 430 : 1490, 560, 290];
		if (layout === 'trio') return [[560, 960, 1360][i], 830, 200];
		if (layout === 'letter') return [1400, 500, 340];
		// count: grid of up to 5 per row on the right
		const n = items.length;
		const cols = Math.min(5, n);
		const rows = Math.ceil(n / 5);
		const r = Math.floor(i / 5);
		const c = i % 5;
		const inRow = r === rows - 1 ? n - r * 5 : cols;
		return [1240 + (c - (inRow - 1) / 2) * 200, 560 + (r - (rows - 1) / 2) * 220, 175];
	};

	return (
		<AbsoluteFill>
			<div style={{position: 'absolute', top: 50, width: '100%', opacity: interpolate(frame, [out, out + 12], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}}>
				<PopWord text={title.text} color={title.color} size={170} startFrame={title.at} />
			</div>
			{layout === 'pair' ? (
				<FloatingBalloon color={hero.color} x={960} y={330} width={300} enterAt={hero.at} seed={scene.from} exitAt={out} />
			) : (
				<Pop at={hero.at} outAt={out} seed={1}>
					<HeroView hero={hero} x={heroAt[layout][0]} y={heroAt[layout][1] + (hero.body ? 60 : 0)} size={heroAt[layout][2] * (hero.body ? 1.3 : 1)} blink={blink} />
				</Pop>
			)}
			{items.map((it, i) => {
				const [x, y, size] = itemPos(i);
				return (
					<Pop key={i} at={it.at} outAt={out} seed={i + 2}>
						<HeroView hero={{kind: it.kind, value: it.value, color: it.color}} x={x} y={y} size={size} blink={blinkAt(frame, i + 3)} />
						{it.label ? <Label text={it.label} color={it.color} x={x} y={y + size / 2 + 10} size={layout === 'letter' ? 90 : 76} /> : null}
					</Pop>
				);
			})}
			{bubble ? (
				<Pop at={bubble.at} outAt={out} seed={5} bob={6}>
					<div style={{position: 'absolute', left: 1220, top: 230, width: 520, height: 250}}>
						<svg width={520} height={250} viewBox="0 0 520 250" style={{position: 'absolute'}}>
							<path d="M60 20 H460 Q500 20 500 60 V170 Q500 210 460 210 H140 L70 245 L95 210 H60 Q20 210 20 170 V60 Q20 20 60 20 Z" fill="#fff" />
						</svg>
						<div style={{position: 'absolute', width: 520, top: 58, textAlign: 'center'}}>
							<span style={{...textStyle(scene.tint, 110), WebkitTextStroke: '0px'}}>{bubble.text}</span>
						</div>
					</div>
				</Pop>
			) : null}
			{caption ? (
				<Pop at={caption.at} outAt={out} bob={4}>
					<div style={{position: 'absolute', top: 840, width: '100%', textAlign: 'center'}}>
						<span style={textStyle(scene.tint, 100)}>{caption.text}</span>
					</div>
				</Pop>
			) : null}
		</AbsoluteFill>
	);
};

const Review: React.FC<{scene: Extract<Scene, {type: 'review'}>}> = ({scene}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const n = scene.entries.length;
	const spacing = Math.min(260, 1760 / n);
	const size = Math.min(200, spacing * 0.85);
	return (
		<AbsoluteFill>
			<div style={{position: 'absolute', top: 70, width: '100%'}}>
				<PopWord text={scene.heading.text} color={scene.heading.color} size={130} startFrame={4} />
			</div>
			{scene.entries.map((e, i) => {
				const x = 960 + (i - (n - 1) / 2) * spacing;
				const hit = frame >= e.at ? 1 + 0.35 * Math.exp(-(frame - e.at) / 10) : 1;
				const label = spring({frame: frame - e.at, fps, config: {damping: 10}});
				return (
					<div key={i}>
						<Pop at={i * 3} seed={i}>
							<HeroView hero={e.hero} x={x} y={460 - (hit - 1) * 100} size={size * hit} blink={blinkAt(frame, i)} />
						</Pop>
						<div style={{position: 'absolute', left: x - spacing / 2, width: spacing, top: 650, textAlign: 'center', transform: `scale(${label})`}}>
							<span style={textStyle(e.hero.color, Math.min(64, spacing * 0.3))}>{e.label}</span>
						</div>
					</div>
				);
			})}
		</AbsoluteFill>
	);
};

const Outro: React.FC<{byeAt: number; top?: string}> = ({byeAt, top = 'Great job!'}) => (
	<AbsoluteFill>
		{RAINBOW.map((c, i) => (
			<FloatingBalloon key={c} color={c} x={260 + i * 233} y={420 + (i % 2) * 70} width={160} enterAt={i * 3} seed={i} exitAt={byeAt + 10 + i * 5} />
		))}
		<div style={{position: 'absolute', top: 130, width: '100%'}}>
			<PopWord text={top} color="#FF8A1F" size={170} startFrame={4} />
		</div>
		<div style={{position: 'absolute', top: 430, width: '100%'}}>
			<PopWord text="Bye bye!" color="#2F8CFF" size={200} startFrame={byeAt} />
		</div>
		<div style={{position: 'absolute', top: 680, width: '100%'}}>
			<PopWord text="See you tomorrow!" color={RAINBOW} size={110} startFrame={byeAt + 20} />
		</div>
	</AbsoluteFill>
);

// ---------------------------------------------------------------- compositions
export const Episode: React.FC<EpisodeProps> = ({scenes, audio, season = 'spring', look = 0}) => {
	const frame = useCurrentFrame();
	const current = scenes.find((s) => frame >= s.from && frame < s.from + s.duration);
	const tint = current && current.type === 'focus' ? current.tint : null;
	const bg: Bg = (current && 'bg' in current && current.bg) || 'day';
	// in a story, the camera leans in towards whoever is speaking, and back out between lines
	const cam = current && current.type === 'story' ? storyCam(current.cam, frame - current.from) : {x: 960, lean: 0};
	const z = 1 + 0.22 * cam.lean;
	const tx = Math.min(0, Math.max(1920 - 1920 * z, 960 - cam.x * z));
	const ty = Math.min(0, Math.max(1080 - 1080 * z, 540 - 560 * z));
	return (
		<Look.Provider value={{season, seed: look}}>
		<AbsoluteFill style={{transform: `translate(${tx}px, ${ty}px) scale(${z})`, transformOrigin: '0 0'}}>
			<Scenery bg={bg} tint={tint} />
			{scenes.map((s, i) => (
				<Sequence key={i} from={s.from} durationInFrames={s.duration}>
					{s.type === 'intro' && <Intro duration={s.duration} title={s.title} />}
					{s.type === 'section' && <Section duration={s.duration} sub={s.sub} text={s.text} heroes={s.heroes} />}
					{s.type === 'focus' && <Focus scene={s} />}
					{s.type === 'review' && <Review scene={s} />}
					{s.type === 'outro' && <Outro byeAt={s.byeAt} top={s.top} />}
					{s.type === 'title' && <TitleCard scene={s} />}
					{s.type === 'story' && <StoryScene scene={s} />}
					{s.type === 'egg' && <EggScene scene={s} />}
					{s.type === 'shadow' && <ShadowScene scene={s} />}
					{s.type === 'dance' && <DanceScene scene={s} />}
				</Sequence>
			))}
			{audio ? <Audio src={staticFile(audio)} /> : null}
		</AbsoluteFill>
		</Look.Provider>
	);
};

/** The daily story's thumbnail: the main character big, the second one beside it, the title in two short lines and
 *  the kind of story as a coloured badge, so every day's picture is different and readable on a small phone. */
const StoryThumbnail: React.FC<EpisodeProps> = ({thumb, season = 'spring', look = 0}) => {
	const [main, second] = thumb.heroes;
	const words = thumb.title.join(' ').split(' ');
	const cut = words.length > 2 ? Math.ceil(words.length / 2) : words.length;
	const lines = [words.slice(0, cut).join(' '), words.slice(cut).join(' ')].filter(Boolean);
	const longest = Math.max(...lines.map((l) => l.length));
	const size = Math.min(170, Math.floor(1700 / Math.max(8, longest)));
	return (
		<Look.Provider value={{season, seed: look}}>
			<AbsoluteFill>
				<Scenery bg={thumb.bg ?? 'day'} tint={null} />
				<AbsoluteFill style={{background: 'radial-gradient(ellipse at 30% 70%, rgba(255,255,255,0) 35%, rgba(0,0,0,0.28) 100%)'}} />
				<Rays x={560} y={700} r={760} color={thumb.rays ?? '#fff6b0'} opacity={0.55} frame={0} count={18} />
				{second ? (
					<div style={{position: 'absolute', inset: 0, transform: 'rotate(5deg)'}}>
						<HeroView hero={second} x={1330} y={second.body ? 770 : 800} size={second.body ? 450 : 320} blink={1} />
					</div>
				) : null}
				{main ? (
					<div style={{position: 'absolute', inset: 0, transform: 'rotate(-4deg)'}}>
						<HeroView hero={main} x={560} y={main.body ? 690 : 720} size={main.body ? 720 : 500} blink={1} />
					</div>
				) : null}
				{thumb.badge ? (
					<div style={{position: 'absolute', left: 50, top: 46, transform: 'rotate(-4deg)', background: thumb.badgeColor ?? '#FF8A1F', borderRadius: 60, padding: '14px 40px', border: '8px solid #fff', boxShadow: '0 10px 0 rgba(0,0,0,0.15)'}}>
						<span style={{...textStyle('#ffffff', 64), WebkitTextStroke: '0px', filter: 'none'}}>{thumb.badge}</span>
					</div>
				) : null}
				<div style={{position: 'absolute', right: 50, top: 190, width: 1050, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6}}>
					{lines.map((line, i) => (
						<div key={i} style={{display: 'flex', transform: `rotate(${i ? 2 : -2}deg)`}}>
							{line.split('').map((ch, k) => (
								<span key={k} style={{...textStyle(RAINBOW[(k + i * 3) % RAINBOW.length], size), WebkitTextStroke: `${Math.round(size / 7)}px #fff`, display: 'inline-block'}}>
									{ch === ' ' ? '\u00a0' : ch}
								</span>
							))}
						</div>
					))}
				</div>
				<div style={{position: 'absolute', right: 40, bottom: 30}}>
					<span style={textStyle('#2F8CFF', 56)}>Bubbly Kids TV</span>
				</div>
			</AbsoluteFill>
		</Look.Provider>
	);
};

export const EpisodeThumbnail: React.FC<EpisodeProps> = (props) => {
	const {thumb, season = 'spring', look = 0} = props;
	if (thumb.badge) return <StoryThumbnail {...props} />;
	const n = thumb.heroes.length;
	return (
		<Look.Provider value={{season, seed: look}}>
		<AbsoluteFill>
			<Scenery bg={thumb.bg ?? 'day'} tint={null} />
			{thumb.title.map((line, i) => (
				<div key={line} style={{position: 'absolute', top: 60 + i * 190, width: '100%', display: 'flex', justifyContent: 'center'}}>
					{line.split('').map((ch, k) => (
						<span key={k} style={{...textStyle(RAINBOW[k % RAINBOW.length], i === 0 ? 200 : Math.min(150, 3000 / line.length)), display: 'inline-block'}}>
							{ch === ' ' ? ' ' : ch}
						</span>
					))}
				</div>
			))}
			{thumb.heroes.map((h, i) => (
				<div key={i} style={{position: 'absolute', inset: 0, transform: `rotate(${(i - (n - 1) / 2) * 4}deg)`}}>
					<HeroView hero={h} x={960 + (i - (n - 1) / 2) * 340} y={h.body ? 760 : 790} size={h.body ? 420 : 300} blink={1} />
				</div>
			))}
			<div style={{position: 'absolute', right: 40, bottom: 30}}>
				<span style={textStyle('#2F8CFF', 60)}>Bubbly Kids TV</span>
			</div>
		</AbsoluteFill>
		</Look.Provider>
	);
};
