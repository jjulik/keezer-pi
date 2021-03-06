drop table if exists token;
create table token (
	token text primary key,
	active integer not null
);

drop table if exists sensor;
create table sensor (
	sensorid integer primary key autoincrement,
	sensortype text,
	description text,
	check (sensortype in ("temperature", "power"))
);

drop table if exists reading;
create table reading (
	readingid integer primary key autoincrement,
	sensorid integer REFERENCES sensor(sensorid),
	[time] text not null,
	value text not null
);

drop table if exists clienterror;
create table clienterror (
	errorid integer primary key autoincrement,
	[time] text not null,
	error text not null
);
