DROP SCHEMA IF EXISTS sensor;
CREATE SCHEMA sensor;
USE sensor;

grant all privileges on sensor.* to 'root'@localhost;  

create table data (
    idData int auto_increment primary key not null,
    val1 int,
    val2 int);

create table classroom (
    classRoom varchar(30) primary key not null,
    openings int,
    floorplan int);
    
create table readings (
    classRoom varchar(30),
    startInstance int,
    endInstance int,
    people int);
    
create table admins (
    adminName varchar(80) primary key,
    pword varchar(80) unique);
    
insert into classroom values ('cr8',3,2);
insert into admins values ('hadi','1234');
insert into readings values ('cr8',0,0,1);