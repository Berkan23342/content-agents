import React from 'react';
import {ALL_ICONS} from './library';
import {mix} from './shapes';

/** How a full-body character is posed on one frame. */
export type Pose = {
	blink: number;
	talk?: number; // 0..1 mouth opening
	walk?: number; // walk-cycle phase in radians (feet step, arms swing)
	arms?: 'down' | 'swing' | 'wave' | 'up' | 'clap' | 'flap';
	frame?: number; // for waving and flapping
};

// body, belly, feet colours of the animals that get a body
const BODY: Record<string, [string, string, string]> = {
	cat: ['#f6a44c', '#ffe1bd', '#d9822b'],
	dog: ['#d9a066', '#f3d8b5', '#8a5a33'],
	cow: ['#ffffff', '#ffd1dc', '#5b5b6b'],
	sheep: ['#ffffff', '#f4f4f4', '#5b5b6b'],
	duck: ['#ffd23f', '#ffe98a', '#ff8a1f'],
	lion: ['#f6c453', '#fde7a8', '#d9822b'],
	chick: ['#ffe14d', '#fff2a8', '#ff8a1f'],
	owl: ['#a06a3c', '#f3d8b5', '#ff8a1f'],
	zebra: ['#ffffff', '#f1f1f1', '#2b2b3a'],
	bunny: ['#f4f0f7', '#ffffff', '#ffb3c6'],
	turtle: ['#86cc62', '#dff7c4', '#5fae42'],
	bear: ['#9a6235', '#e0a877', '#6e4424'],
	pig: ['', '', ''],
	frog: ['', '', ''],
};

// where the mouth is on each head (200x200 head art)
const MOUTH: Record<string, [number, number]> = {
	cat: [100, 141],
	dog: [100, 152],
	cow: [100, 157],
	sheep: [100, 146],
	duck: [100, 134],
	lion: [100, 143],
	chick: [100, 126],
	owl: [100, 120],
	zebra: [100, 162],
	bunny: [100, 148],
	turtle: [100, 152],
	bear: [100, 152],
	pig: [100, 148],
	frog: [100, 146],
};

export const hasBody = (name: string) => name in BODY;

const Arm: React.FC<{x: number; angle: number; color: string; hand: string}> = ({x, angle, color, hand}) => (
	<g transform={`rotate(${angle} ${x} 196)`}>
		<rect x={x - 11} y={192} width={22} height={58} rx={11} fill={color} />
		<circle cx={x} cy={252} r={14} fill={hand} />
	</g>
);

const armAngles = (pose: Pose): [number, number] => {
	const f = pose.frame ?? 0;
	const w = pose.walk ?? 0;
	switch (pose.arms) {
		case 'swing':
			return [18 + Math.sin(w) * 28, -18 + Math.sin(w) * 28];
		case 'wave':
			return [16, -150 + Math.sin(f * 0.45) * 22];
		case 'up':
			return [150 + Math.sin(f * 0.5) * 12, -150 - Math.sin(f * 0.5) * 12];
		case 'clap': {
			const c = Math.abs(Math.sin(w));
			return [-28 + c * 70, 28 - c * 70];
		}
		case 'flap': {
			const a = 70 + Math.sin(f * 0.9) * 45;
			return [a, -a];
		}
		default:
			return [16, -16];
	}
};

/** A full-body animal: the head art from the icon library on a little body with arms and feet. viewBox 200x300. */
export const Critter: React.FC<{name: string; color: string; height: number; pose: Pose}> = ({name, color, height, pose}) => {
	const Head = ALL_ICONS[name];
	let [body, belly, feet] = BODY[name];
	if (!body) {
		body = color;
		belly = mix(color, '#ffffff', 0.45);
		feet = mix(color, '#000000', 0.2);
	}
	const arm = mix(body, '#000000', body === '#ffffff' ? 0.06 : 0.08);
	const w = pose.walk ?? 0;
	const liftL = pose.walk === undefined ? 0 : Math.max(0, Math.sin(w)) * 16;
	const liftR = pose.walk === undefined ? 0 : Math.max(0, -Math.sin(w)) * 16;
	const [aL, aR] = armAngles(pose);
	const talk = pose.talk ?? 0;
	const [mx, my] = MOUTH[name];
	const outline = body === '#ffffff' || body === '#f4f0f7' ? '#e2e2ea' : mix(body, '#000000', 0.14);
	return (
		<svg width={height * (2 / 3)} height={height} viewBox="0 0 200 300" style={{overflow: 'visible'}}>
			<ellipse cx={76} cy={284 - liftL} rx={25} ry={13} fill={feet} />
			<ellipse cx={124} cy={284 - liftR} rx={25} ry={13} fill={feet} />
			<ellipse cx={100} cy={224} rx={52} ry={54} fill={body} stroke={outline} strokeWidth={3} />
			<ellipse cx={100} cy={236} rx={33} ry={35} fill={belly} />
			{name === 'cow' ? <path d="M64 206 Q80 196 86 214 Q76 230 62 220 Z" fill="#2b2b3a" /> : null}
			{name === 'zebra'
				? [200, 222, 244].map((y) => <path key={y} d={`M50 ${y} Q66 ${y - 6} 74 ${y + 4} Q62 ${y + 6} 50 ${y + 10} Z M150 ${y} Q134 ${y - 6} 126 ${y + 4} Q138 ${y + 6} 150 ${y + 10} Z`} fill="#2b2b3a" />)
				: null}
			<ellipse cx={72} cy={200} rx={10} ry={18} fill="#fff" opacity={0.18} transform="rotate(25 72 200)" />
			<Arm x={54} angle={aL} color={arm} hand={arm} />
			<Arm x={146} angle={aR} color={arm} hand={arm} />
			<Head color={color} blink={pose.blink} headOnly />
			{talk > 0.08 ? (
				<g>
					<ellipse cx={mx} cy={my + 2} rx={10 + talk * 4} ry={2 + talk * 12} fill="#8a2b3d" />
					{talk > 0.4 ? <ellipse cx={mx} cy={my + 6 + talk * 6} rx={6} ry={3 + talk * 2} fill="#ff7a9c" /> : null}
				</g>
			) : null}
		</svg>
	);
};

/** Fruit, food and shapes get stick arms, legs and sneakers so they can dance. viewBox 200x290. */
export const Buddy: React.FC<{art: React.ReactNode; height: number; pose: Pose; shoe: string}> = ({art, height, pose, shoe}) => {
	const w = pose.walk ?? 0;
	const liftL = Math.max(0, Math.sin(w)) * 14;
	const liftR = Math.max(0, -Math.sin(w)) * 14;
	const [aL, aR] = armAngles(pose);
	const limb = (x: number, angle: number) => (
		<g transform={`rotate(${angle} ${x} 120)`}>
			<line x1={x} y1={120} x2={x} y2={178} stroke="#2b2b3a" strokeWidth={7} strokeLinecap="round" />
			<circle cx={x} cy={184} r={13} fill="#fff" stroke="#2b2b3a" strokeWidth={4} />
		</g>
	);
	return (
		<svg width={height * (200 / 290)} height={height} viewBox="0 0 200 290" style={{overflow: 'visible'}}>
			<path d={`M84 175 L80 ${262 - liftL}`} stroke="#2b2b3a" strokeWidth={8} strokeLinecap="round" />
			<path d={`M116 175 L120 ${262 - liftR}`} stroke="#2b2b3a" strokeWidth={8} strokeLinecap="round" />
			<ellipse cx={70} cy={268 - liftL} rx={22} ry={12} fill={shoe} />
			<ellipse cx={130} cy={268 - liftR} rx={22} ry={12} fill={shoe} />
			<svg x={0} y={0} width={200} height={200} viewBox="0 0 200 200" style={{overflow: 'visible'}}>
				{art}
			</svg>
			{limb(26, aL + 20)}
			{limb(174, aR - 20)}
		</svg>
	);
};
