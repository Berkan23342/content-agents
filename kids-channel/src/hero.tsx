import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {textStyle} from './common';
import {Buddy, Critter, Pose, hasBody} from './critter';
import {ALL_ICONS, Icon, ShapeFace} from './library';
import {Balloon, mix} from './shapes';

// ---------------------------------------------------------------- heroes (written by the Python builders)
export type Hero = {
	kind: 'balloon' | 'icon' | 'shape' | 'number' | 'letter' | 'egg';
	value: string; // icon/shape name, digit, letter, or "pattern|accent" for eggs
	color: string;
	shadow?: boolean; // draw as a black silhouette
	body?: boolean; // full-body character (animals get a body, food and shapes get arms and legs)
};

/** A full-body character standing with its feet on (x, feetY). */
export const Character: React.FC<{hero: Hero; x: number; feetY: number; height: number; pose: Pose}> = ({hero, x, feetY, height, pose}) => {
	let node: React.ReactNode;
	let width: number;
	if (hero.kind === 'icon' && hasBody(hero.value)) {
		width = height * (2 / 3);
		node = <Critter name={hero.value} color={hero.color} height={height} pose={pose} />;
	} else {
		width = height * (200 / 290);
		const Comp = ALL_ICONS[hero.value];
		const art =
			hero.kind === 'shape' ? (
				<ShapeFace shape={hero.value} color={hero.color} size={200} blink={pose.blink} />
			) : Comp ? (
				<Comp color={hero.color} blink={pose.blink} />
			) : null;
		node = <Buddy art={art} height={height} pose={pose} shoe={hero.color === '#FF3B3B' ? '#2F8CFF' : '#FF3B3B'} />;
	}
	return (
		<div
			style={{
				position: 'absolute',
				left: x - width / 2,
				top: feetY - height,
				width,
				height,
				filter: hero.shadow ? 'brightness(0) opacity(0.82)' : 'drop-shadow(0 10px 0 rgba(0,0,0,0.10))',
			}}
		>
			{node}
		</div>
	);
};

const EGG = 'M100 8 C 158 8, 192 112, 192 160 C 192 222, 150 254, 100 254 C 50 254, 8 222, 8 160 C 8 112, 42 8, 100 8 Z';
const CRACK = 'M2 134 L30 118 L52 144 L76 120 L100 146 L124 118 L148 144 L170 120 L198 136';
const ABOVE = `${CRACK} L198 0 L2 0 Z`;
const BELOW = `${CRACK} L198 262 L2 262 Z`;

const EggPattern: React.FC<{pattern: string; accent: string}> = ({pattern, accent}) => {
	const cells: React.ReactNode[] = [];
	if (pattern === 'stripes') {
		for (let y = 40; y < 260; y += 56) cells.push(<rect key={y} x={0} y={y} width={200} height={20} fill={accent} />);
	} else if (pattern === 'zigzag') {
		for (let y = 50; y < 260; y += 62) {
			const d = Array.from({length: 11}, (_, i) => `${i === 0 ? 'M' : 'L'}${i * 20} ${y + (i % 2 ? -14 : 14)}`).join(' ');
			cells.push(<path key={y} d={d} fill="none" stroke={accent} strokeWidth={12} strokeLinejoin="round" />);
		}
	} else {
		for (let row = 0; row < 7; row++) {
			for (let col = 0; col < 6; col++) {
				const x = col * 40 + (row % 2) * 20;
				const y = 22 + row * 38;
				const key = `${row}-${col}`;
				if (pattern === 'stars') {
					const pts = Array.from({length: 10}, (_, i) => {
						const r = i % 2 ? 5 : 12;
						const a = (Math.PI / 5) * i - Math.PI / 2;
						return `${x + r * Math.cos(a)},${y + r * Math.sin(a)}`;
					}).join(' ');
					cells.push(<polygon key={key} points={pts} fill={accent} />);
				} else if (pattern === 'hearts') {
					cells.push(
						<path key={key} d={`M${x} ${y + 9} C ${x - 14} ${y}, ${x - 10} ${y - 12}, ${x} ${y - 4} C ${x + 10} ${y - 12}, ${x + 14} ${y}, ${x} ${y + 9} Z`} fill={accent} />,
					);
				} else {
					cells.push(<circle key={key} cx={x} cy={y} r={9} fill={accent} />);
				}
			}
		}
	}
	return <>{cells}</>;
};

/** A patterned surprise egg. crack: 0..1 how much of the crack is drawn, open: 0..1 lid flying off. */
export const EggView: React.FC<{value: string; color: string; size: number; crack?: number; open?: number; id: string}> = ({
	value,
	color,
	size,
	crack = 0,
	open = 0,
	id,
}) => {
	const [pattern, accent = '#ffffff'] = value.split('|');
	const body = (
		<>
			<path d={EGG} fill={color} />
			<g clipPath={`url(#egg-${id})`}>
				<EggPattern pattern={pattern} accent={accent} />
				<ellipse cx={150} cy={190} rx={70} ry={90} fill={mix(color, '#000000', 0.18)} opacity={0.16} />
			</g>
			<ellipse cx={62} cy={70} rx={16} ry={32} fill="#fff" opacity={0.45} transform="rotate(25 62 70)" />
		</>
	);
	return (
		<svg width={size * 0.77} height={size} viewBox="0 0 200 262" style={{overflow: 'visible'}}>
			<defs>
				<clipPath id={`egg-${id}`}>
					<path d={EGG} />
				</clipPath>
				<clipPath id={`top-${id}`}>
					<path d={ABOVE} />
				</clipPath>
				<clipPath id={`bot-${id}`}>
					<path d={BELOW} />
				</clipPath>
			</defs>
			<g clipPath={`url(#bot-${id})`} opacity={1 - Math.max(0, open - 0.6) * 2.5}>
				{body}
			</g>
			<g
				clipPath={`url(#top-${id})`}
				transform={`translate(${open * 140} ${-open * 260}) rotate(${open * 50} 100 130)`}
				opacity={1 - open * 0.8}
			>
				{body}
			</g>
			{crack > 0 && open === 0 ? (
				<path d={CRACK} fill="none" stroke="#2b2b3a" strokeWidth={5} strokeLinejoin="round" pathLength={1} strokeDasharray={`${crack} 1`} />
			) : null}
		</svg>
	);
};

/** Draws any hero centred on (x, y) with the given visual size. */
export const HeroView: React.FC<{hero: Hero; x: number; y: number; size: number; blink: number}> = ({hero, x, y, size, blink}) => {
	if (hero.body) return <Character hero={hero} x={x} feetY={y + size / 2} height={size} pose={{blink, arms: 'down'}} />;
	const box = (child: React.ReactNode, w = size, h = size) => (
		<div
			style={{
				position: 'absolute',
				left: x - w / 2,
				top: y - h / 2,
				width: w,
				height: h,
				display: 'flex',
				alignItems: 'center',
				justifyContent: 'center',
				filter: hero.shadow ? 'brightness(0) opacity(0.82)' : 'drop-shadow(0 10px 0 rgba(0,0,0,0.10))',
			}}
		>
			{child}
		</div>
	);
	switch (hero.kind) {
		case 'balloon':
			return box(<Balloon color={hero.color} width={size * 0.62} blink={blink} />, size * 0.62, size);
		case 'icon':
			return box(<Icon name={hero.value} color={hero.color} size={size} blink={blink} />);
		case 'shape':
			return box(<ShapeFace shape={hero.value} color={hero.color} size={size} blink={blink} />);
		case 'egg':
			return box(<EggView value={hero.value} color={hero.color} size={size} id={`h${Math.round(x)}-${Math.round(y)}`} />, size * 0.77, size);
		case 'number':
			return box(<span style={textStyle(hero.color, size * 0.95)}>{hero.value}</span>, size * 1.4, size);
		case 'letter':
			return box(
				<span style={textStyle(hero.color, size * 0.78)}>
					{hero.value}
					<span style={{fontSize: size * 0.5}}>{hero.value.toLowerCase()}</span>
				</span>,
				size * 1.6,
				size,
			);
	}
};

/** Springs in at `at`, bobs while visible, shrinks away at `outAt`. */
export const Pop: React.FC<{at: number; outAt?: number; seed?: number; children: React.ReactNode; bob?: number}> = ({
	at,
	outAt,
	seed = 0,
	children,
	bob = 10,
}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const s = spring({frame: frame - at, fps, config: {damping: 8, stiffness: 140}});
	const out = outAt === undefined ? 1 : interpolate(frame, [outAt, outAt + 12], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const dy = Math.sin((frame + seed * 17) / 12) * bob * Math.min(1, s);
	const rot = Math.sin((frame + seed * 11) / 20) * 3;
	return <AbsoluteFill style={{transform: `translateY(${dy}px) rotate(${rot}deg) scale(${s * out})`, transformOrigin: '50% 55%'}}>{children}</AbsoluteFill>;
};

/** White speech bubble whose tail points down at (x, y). */
export const SpeechBubble: React.FC<{text: string; color: string; x: number; y: number; scale?: number; size?: number}> = ({
	text,
	color,
	x,
	y,
	scale = 1,
	size = 64,
}) => {
	const w = Math.min(1100, Math.max(220, text.length * size * 0.56 + 90));
	const h = size + 70;
	const left = Math.max(20, Math.min(1900 - w, x - w / 2));
	const top = Math.max(16, y - h - 40);
	const tailX = Math.max(left + 40, Math.min(left + w - 40, x));
	return (
		<div style={{position: 'absolute', left, top, width: w, height: h + 40, transform: `scale(${scale})`, transformOrigin: `${tailX - left}px ${h + 40}px`}}>
			<svg width={w} height={h + 40} style={{position: 'absolute', overflow: 'visible'}}>
				<rect x={0} y={0} width={w} height={h} rx={h / 2.4} fill="#fff" />
				<path d={`M${tailX - left - 26} ${h - 4} L${tailX - left} ${h + 38} L${tailX - left + 26} ${h - 4} Z`} fill="#fff" />
			</svg>
			<div style={{position: 'absolute', width: w, top: (h - size) / 2 - 2, textAlign: 'center'}}>
				<span style={{...textStyle(color, size), WebkitTextStroke: '0px', filter: 'none'}}>{text}</span>
			</div>
		</div>
	);
};
