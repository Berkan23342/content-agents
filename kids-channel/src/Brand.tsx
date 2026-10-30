import React from 'react';
import {AbsoluteFill} from 'remotion';
import {textStyle} from './common';
import {Balloon} from './shapes';

/** 800x800 channel avatar (YouTube crops it to a circle). */
export const Logo: React.FC = () => (
	<AbsoluteFill style={{background: 'radial-gradient(circle at 50% 35%, #bfeaff 0%, #6cc6ff 60%, #3aa5f2 100%)'}}>
		{[
			{c: '#FF3B3B', x: 250, y: 95, r: -14, w: 210},
			{c: '#2F8CFF', x: 550, y: 95, r: 14, w: 210},
			{c: '#FFC92E', x: 400, y: 45, r: 0, w: 245},
		].map((b) => (
			<div key={b.c} style={{position: 'absolute', left: b.x - b.w / 2, top: b.y, transform: `rotate(${b.r}deg)`, transformOrigin: '50% 100%'}}>
				<Balloon color={b.c} width={b.w} />
			</div>
		))}
		<div style={{position: 'absolute', top: 470, width: '100%', display: 'flex', justifyContent: 'center'}}>
			{'Bubbly'.split('').map((ch, i) => (
				<span key={i} style={{...textStyle(['#FF3B3B', '#FF8A1F', '#FFC92E', '#3CC75A', '#9B5CFF', '#FF6FB5'][i], 150), display: 'inline-block'}}>
					{ch}
				</span>
			))}
		</div>
		<div style={{position: 'absolute', top: 625, width: '100%', textAlign: 'center'}}>
			<span style={textStyle('#2F8CFF', 82)}>Kids TV</span>
		</div>
	</AbsoluteFill>
);
