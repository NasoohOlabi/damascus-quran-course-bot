import { DataTypes, InitOptions, Model, ModelAttributes, ModelStatic } from 'sequelize';
import { sequelize } from '../config/database';

export abstract class BaseEntity extends Model {
	declare id: number;
	declare createdAt: Date;
	declare createdBy?: string;
	declare modifiedAt?: Date;
	declare modifiedBy?: string;

	static baseAttributes: ModelAttributes = {
		id: {
			type: DataTypes.INTEGER,
			primaryKey: true,
			autoIncrement: true,
		},
		createdAt: {
			type: DataTypes.DATE,
			allowNull: false,
			defaultValue: DataTypes.NOW,
		},
		createdBy: {
			type: DataTypes.STRING(255),
			allowNull: true,
		},
		modifiedAt: {
			type: DataTypes.DATE,
			allowNull: true,
		},
		modifiedBy: {
			type: DataTypes.STRING(255),
			allowNull: true,
		},
	};

	static baseOptions: InitOptions = {
		sequelize,
		timestamps: false,
		underscored: true,
		modelName: 'Base', // This will be overridden by child classes
		tableName: 'bases', // This will be overridden by child classes
	};

	static initModel<T extends ModelStatic<Model>>(this: T, attributes: ModelAttributes, config: InitOptions) {
		this.init(
			{ ...this.getAttributes(), ...attributes },
			{ ...this.baseOptions, ...config }
		);
		return this;
	}
}