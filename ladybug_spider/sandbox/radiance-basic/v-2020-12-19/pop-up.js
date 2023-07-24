/* global THREE, THR, RAD, divPopUp */
// jshint esversion: 6

// Copyright 2018 Ladybug Tools authors. MIT License

const POP = {};
let line;

const particleMaterial = new THREE.SpriteMaterial( { color: 0xff0000 } );
POP.particle = new THREE.Sprite( particleMaterial );

POP.getPopUpHtml = function () {

	POP.mouse = new THREE.Vector2();
	POP.raycaster = new THREE.Raycaster();
	POP.objects = RAD.meshes.children;
	POP.intersected = undefined;
	POP.divTarget = divPopUp;

	THR.renderer.domElement.addEventListener( 'pointerdown', POP.onDocumentMouseDown, false );
	THR.renderer.domElement.addEventListener( 'touchstart', POP.onDocumentTouchStart, false ); // for mobile

	var geometry = new THREE.BufferGeometry();
	geometry.setAttribute( 'position', new THREE.BufferAttribute( new Float32Array( 4 * 3 ), 3 ) );

	var material = new THREE.LineBasicMaterial( { color: 0xffffff, linewidth: 2, transparent: true } );

	line = new THREE.Line( geometry, material );
	THR.scene.add( line );

	POP.particle.scale.x = POP.particle.scale.y = 0.03 * THR.radius;
	POP.particle.visible = false;
	THR.scene.add( POP.particle );

	const htm =
		`
		<div id = "divPopUpLog"  ></div>

		<div id = "divPopUpDataXXX" >

			<p>Item data appears here when the pointer is over a data point</p>

			<p>Axis RGB = XYZ directions</p>

			<p>Spacebar: click to stop spinning</p>

			<p>Use one|two|three fingers to rotate|zoom|pan display in 3D. Or left|scroll|right with your pointing device</p>

			<p>Press Control-Shift-J|Command-Option-J to see if the JavaScript console reports any errors</p>

		</div>

	`;

	return htm;

};



POP.onDocumentTouchStart = function ( event ) {

	event.preventDefault();

	event.clientX = event.touches[ 0 ].clientX;
	event.clientY = event.touches[ 0 ].clientY;

	POP.onDocumentMouseDown( event );

};



POP.onDocumentMouseDown = function ( event ) {

	event.preventDefault();

	//	POP.mouse.x = ( event.clientX / THR.renderer.domElement.style.width ) * 2 - 1;
	//	POP.mouse.y = - ( event.clientY / THR.renderer.domElement.style.height ) * 2 + 1;

	POP.mouse.x = ( event.clientX / window.innerWidth ) * 2 - 1;
	POP.mouse.y = - ( event.clientY / window.innerHeight ) * 2 + 1;

	POP.raycaster.setFromCamera( POP.mouse, THR.camera );

	POP.intersects = POP.raycaster.intersectObjects( POP.objects );

	//console.log( 'intersects', intersects );

	if ( POP.intersects.length > 0 ) {

		POP.intersected = POP.intersects[ 0 ].object;

		POP.faceIndex = POP.intersects[ 0 ].faceIndex;
		//intersected.material.color.setHex( Math.random() * 0xffffff );

		POP.divTarget.style.display = '';

		POP.getIntersectedVertexBufferGeometry();

		POP.divTarget.innerHTML = POP.getIntersectedDataHtml();


	} else {

		POP.intersected = null;

		POP.divTarget.style.display = 'none';

		line.visible = false;
		POP.particle.visible = false;
		document.body.style.cursor = 'auto';

	}

};



POP.getIntersectedVertexBufferGeometry = function () {

	var face = POP.intersects[ 0 ].face;

	// https://stackoverflow.com/questions/36017079/three-js-get-the-position-of-a-single-face-of-a-tessellated-object
	//face.color.setHex( 0xcc0000 ); // nope - must update the attributes
	//intersected.geometry.colorsNeedUpdate = true;
	//console.log( 'intersected', intersected );

	var linePosition = line.geometry.attributes.position;
	meshPosition = POP.intersected.geometry.attributes.position;

	linePosition.copyAt( 0, meshPosition, face.a );
	linePosition.copyAt( 1, meshPosition, face.b );
	linePosition.copyAt( 2, meshPosition, face.c );
	linePosition.copyAt( 3, meshPosition, face.a );

	POP.intersected.updateMatrix();

	line.geometry.applyMatrix4( POP.intersected.matrix );
	line.visible = true;

	POP.particle.position.copy( POP.intersects[ 0 ].point );
	POP.particle.visible = true;

};



POP.getIntersectedVertexGeometry = function () {

	var vertices = intersected.geometry.vertices;
	var dis = 1000000000;
	var ip = POP.intersects[ 0 ].point;
	var pt, index;

	for ( var i = 0; i < vertices.length; i++ ) {

		var vertex = vertices[ i ].clone();
		vertex.applyMatrix4( intersected.matrixWorld );
		var d = vertex.distanceTo( ip );

		if ( d < dis ) {

			dis = d;
			pt = vertex;
			index = i;

		}

	}

	POP.particle.position.copy( intersects[ 0 ].point );


	//console.log( 'interested', pt, intersects[ 0 ] );

};



POP.getIntersectedDataHtml = function ( intersected, intersects ) {

	const triangleParent = RAD.triangleParent[intersected.faceIndex ];
	//console.log( 'triangleParent', triangleParent );

	const surface = POP.intersected.userData.name ? POP.intersected.userData : triangleParent;
	//console.log( 'surface', surface );

	const surfaceText = JSON.stringify( surface, null, 2 ).slice( 2, -2 ).replace( /"/g, '' )
		.replace( /(\D),/g, '$1<br>' ).replace( /vertices:/, 'vertices:<br>' );

	let materialText;

	if ( RAD.json.materials.length > 0 ) {

		const materialJson = RAD.json.materials.find( item => item.name === triangleParent.modifier );

		materialText = materialJson ?
			JSON.stringify( materialJson, null, 2 ).slice( 2, -2 ).replace( /"/g, '' ).replace( /(\D),/g, '$1<br>' )
			:
			"";

	} else {

		materialText =
			`
			name: ${ RAD.colors[ triangleParent.modifier ] }<br>
			color #${ POP.intersected.currentHex }
		`;

	}


	htm =
		`
		<div><b>Geometry</b></div>
		${ surfaceText }
		<div><b>Material</b></div>
		${ materialText }
		<div><b>Three.js</b></div>
		<div>
		name: ${ POP.intersected.name }<br>
		type: ${ POP.intersected.geometry.type }<br>
		index: ${ POP.faceIndex }<br>
		point x: ${ POP.intersects[ 0 ].point.x.toFixed( 2 ) } y: ${ POP.intersects[ 0 ].point.y.toFixed( 2 ) } z: ${ POP.intersects[ 0 ].point.z.toFixed( 2 ) }<br>
	</div>	`;

	return htm;

};
