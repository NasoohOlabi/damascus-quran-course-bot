
import { DataTypes } from 'sequelize';
import { sequelize } from '../config/database';
import { BaseEntity } from './BaseEntity';


// 2. Child model implementation example
class User extends BaseEntity {
	declare username: string;
	declare email: string;

	static initModel() {
		const attributes = {
			...this.getBaseAttributes(), // Inherit base attributes
			username: {
				type: DataTypes.STRING,
				allowNull: false,
			},
			email: {
				type: DataTypes.STRING,
				allowNull: false,
				unique: true,
			},
		};

		super.init(attributes, {
			...this.getBaseConfig(),
			modelName: 'User',
			tableName: 'users', // Explicit table name
		});
	}
}

// Initialize the child model
User.initModel();
