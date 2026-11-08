import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {BrainLogo, Quiz, QuizProps} from './Quiz';
import {Snack, SnackProps} from './Snack';

// Real props come from build/<id>/props.json via `--props`; this is only a Studio placeholder.
const placeholder: QuizProps = {
	durationInFrames: 90,
	audio: '',
	theme: {a: '#2563EB', b: '#7C3AED', accent: '#FACC15'},
	total: 5,
	scenes: [{type: 'hook', from: 0, duration: 90, title: ['GUESS THE', 'FLAG!'], sub: 'CAN YOU GET 5/5?'}],
};

const snackPlaceholder: SnackProps = {
	durationInFrames: 90,
	audio: '',
	format: 'why',
	title: 'Why Is the Sky Blue?',
	theme: {a: '#2563EB', b: '#7C3AED', accent: '#FACC15'},
	beats: [{from: 0, duration: 90, visual: {kind: 'hook', emoji: '🌤️', text: 'Why is the sky blue?'}}],
	chunks: [],
	endAt: 999,
};

const Avatar: React.FC = () => (
	<div style={{width: 800, height: 800, background: 'linear-gradient(160deg, #7C3AED, #DB2777)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
		<BrainLogo size={560} />
	</div>
);

const Root: React.FC = () => (
	<>
		<Composition
			id="Quiz"
			component={Quiz}
			defaultProps={placeholder}
			calculateMetadata={({props}) => ({durationInFrames: props.durationInFrames})}
			durationInFrames={90}
			fps={30}
			width={1080}
			height={1920}
		/>
		<Composition
			id="Snack"
			component={Snack}
			defaultProps={snackPlaceholder}
			calculateMetadata={({props}) => ({durationInFrames: props.durationInFrames})}
			durationInFrames={90}
			fps={30}
			width={1080}
			height={1920}
		/>
		<Composition id="Avatar" component={Avatar} durationInFrames={1} fps={30} width={800} height={800} />
	</>
);

registerRoot(Root);
