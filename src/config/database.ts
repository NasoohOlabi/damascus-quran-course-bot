require('dotenv').config();
import { Sequelize } from "sequelize";
console.log(`process.env.DB_NAME = `, process.env.DB_NAME);
console.log(`process.env.DB_USER = `, process.env.DB_USER);
console.log(`process.env.DB_PASSWORD = `, process.env.DB_PASSWORD);
console.log(`process.env.DB_HOST = `, process.env.DB_HOST);

export const sequelize = new Sequelize(
	process.env.DB_NAME!,
	process.env.DB_USER!,
	process.env.DB_PASSWORD,
	{
		host: process.env.DB_HOST,
		dialect: 'mysql',
		logging: false, // Disable logging SQL queries to the console (optional)
	}
);
